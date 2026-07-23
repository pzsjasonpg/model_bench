"""Subprocess management for running test scripts."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

_logger = logging.getLogger(__name__)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LogLine, SubTask, TestRun, utc_now
from .parser import parse_metrics
from .params import get_test_type
from ..ws.logs import ws_manager


# Track running processes so they can be stopped
_running_processes: Dict[int, asyncio.subprocess.Process] = {}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _param_to_flag(key: str) -> str:
    """Convert snake_case param key to --kebab-case CLI flag."""
    return "--" + key.replace("_", "-")


def _build_command(params: Dict[str, Any], test_type: str):
    """Build the command args list from merged params."""
    info = get_test_type(test_type)
    script = info["script"] if info else "src.main"
    category = info["category"] if info else "chat"

    python_exe = sys.executable

    # Determine the base command
    if script == "src.main":
        cmd_parts = [python_exe, "-m", "src.main"]
        if category == "embedding":
            cmd_parts.extend(["--mode", "embedding"])
    else:
        cmd_parts = [python_exe, script]

    # Build params, skipping internal/non-CLI keys
    skip_keys = {"sweep_key", "sweep_values", "fixed_params",
                 "sweep_params", "model_a_url_base", "model_b_url_base"}

    for key, value in sorted(params.items()):
        if key in skip_keys:
            continue

        flag = _param_to_flag(key)

        if isinstance(value, bool):
            if value:
                cmd_parts.append(flag)
        elif value is not None and value != "" and value is not False:
            cmd_parts.append(flag)
            # For src.main tests, append /chat/completions to base_url
            # (OpenAIAdapter uses it directly; EmbeddingAdapter replaces with /embeddings)
            if key == "base_url" and script == "src.main":
                url = str(value)
                if not url.endswith("/chat/completions"):
                    url = url.rstrip("/") + "/chat/completions"
                cmd_parts.append(url)
            else:
                cmd_parts.append(str(value))

    return cmd_parts


def _build_mtqs_command(params: Dict[str, Any]):
    """Special command builder for mtqs test type. Returns list of args."""
    python_exe = sys.executable

    cmd_parts = [
        python_exe, "tests/mtqs/main-new.py",
        "--excel-file", str(params.get("excel_file", "data/mtqs/语种语料V2.xlsx")),
    ]

    # model-a-url: append /chat/completions
    model_a_url = params.get("model_a_url", "")
    cmd_parts.extend(["--model-a-url", model_a_url + "/chat/completions" if not model_a_url.endswith("/chat/completions") else model_a_url])

    # model-b-url: append /chat/completions
    model_b_url = params.get("model_b_url", "")
    cmd_parts.extend(["--model-b-url", model_b_url + "/chat/completions" if not model_b_url.endswith("/chat/completions") else model_b_url])

    if params.get("concurrency"):
        cmd_parts.extend(["--concurrency", str(params["concurrency"])])
    if params.get("translate_model"):
        cmd_parts.extend(["--translate-model", str(params["translate_model"])])
    if params.get("evaluate_model"):
        cmd_parts.extend(["--evaluate-model", str(params["evaluate_model"])])

    return cmd_parts


async def _save_log(db: AsyncSession, test_run_id: int, subtask_id: int,
                    line: str, timestamp: str):
    """Save a log line to DB."""
    log_line = LogLine(
        test_run_id=test_run_id,
        subtask_id=subtask_id,
        line=line,
        timestamp=timestamp,
    )
    db.add(log_line)
    await db.flush()


async def run_test(test_run_id: int, db: AsyncSession):
    """Execute all subtasks for a given test run sequentially."""
    _logger.info(f"run_test started for test_run_id={test_run_id}")
    # Load test run
    result = await db.execute(select(TestRun).where(TestRun.id == test_run_id))
    test_run = result.scalar_one_or_none()
    if not test_run:
        _logger.warning(f"TestRun {test_run_id} not found in DB")
        return
    _logger.info(f"TestRun {test_run_id} loaded, status={test_run.status}")

    # Load subtasks ordered by seq
    sub_result = await db.execute(
        select(SubTask).where(SubTask.test_run_id == test_run_id).order_by(SubTask.seq)
    )
    subtasks = sub_result.scalars().all()

    if not subtasks:
        test_run.status = "failed"
        test_run.error_message = "No subtasks found"
        test_run.finished_at = utc_now()
        await db.flush()
        return

    test_run.status = "running"
    test_run.started_at = utc_now()
    await db.flush()

    for subtask in subtasks:
        # Check if test was stopped externally
        await db.refresh(test_run)
        if test_run.status == "stopped":
            break

        subtask.status = "running"
        subtask.started_at = utc_now()
        await db.flush()

        await ws_manager.broadcast_status(test_run_id, subtask.seq, "running")

        collected_lines: list = []
        process = None
        try:
            # Build command
            if test_run.test_type == "mtqs":
                cmd_list = _build_mtqs_command(json.loads(subtask.params))
            else:
                cmd_list = _build_command(json.loads(subtask.params), test_run.test_type)

            full_command = " ".join(cmd_list)
            subtask.command = full_command
            await db.flush()

            # Log the command
            timestamp = utc_now()
            cmd_line = f"[CMD] {full_command}"
            collected_lines.append(cmd_line)
            await _save_log(db, test_run_id, subtask.seq, cmd_line, timestamp)
            await ws_manager.broadcast_log(test_run_id, subtask.seq, cmd_line, timestamp)

            _logger.info(f"Spawning subprocess for subtask seq={subtask.seq}: {full_command}")
            # Spawn subprocess with UTF-8 encoding for stdout
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=PROJECT_ROOT,
                env=env,
            )
            subtask.pid = process.pid
            _running_processes[test_run_id] = process
            await db.flush()
            _logger.info(f"Subprocess pid={process.pid} spawned, reading output...")

            # Read stdout line by line
            async for line_bytes in process.stdout:
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\n").rstrip("\r")
                if not line:
                    continue
                collected_lines.append(line)
                timestamp = utc_now()
                await _save_log(db, test_run_id, subtask.seq, line, timestamp)
                await ws_manager.broadcast_log(test_run_id, subtask.seq, line, timestamp)

            await process.wait()

            # Parse metrics
            metrics = parse_metrics(collected_lines)
            subtask.result = json.dumps(metrics, ensure_ascii=False)
            subtask.finished_at = utc_now()

            if process.returncode != 0 or metrics.get("_has_errors"):
                subtask.status = "failed"
                if process.returncode != 0:
                    metrics["_exit_code"] = process.returncode
                    subtask.result = json.dumps(metrics, ensure_ascii=False)
            else:
                subtask.status = "completed"

            # Clean up result keys that start with _ for the broadcast
            clean_result = {k: v for k, v in metrics.items() if not k.startswith("_")}
            await ws_manager.broadcast_status(test_run_id, subtask.seq, subtask.status, clean_result)

        except asyncio.CancelledError:
            subtask.status = "stopped"
            subtask.finished_at = utc_now()
            subtask.result = json.dumps({"_stopped": True}, ensure_ascii=False)
            if process and process.returncode is None:
                try:
                    process.terminate()
                except Exception:
                    pass
            await ws_manager.broadcast_status(test_run_id, subtask.seq, "stopped")
            break

        except Exception as e:
            subtask.status = "failed"
            subtask.finished_at = utc_now()
            subtask.result = json.dumps({"_error": str(e)}, ensure_ascii=False)
            await ws_manager.broadcast_status(test_run_id, subtask.seq, "failed", {"error": str(e)})

        finally:
            _running_processes.pop(test_run_id, None)
            test_run.completed_subtasks += 1
            await db.flush()

    # Finalize test run
    await db.refresh(test_run)
    if test_run.status == "stopped":
        pass  # Already set
    elif all(s.status in ("completed", "failed", "stopped") for s in subtasks):
        if any(s.status == "failed" for s in subtasks):
            # If all failed, mark as failed; if some completed, mark as completed
            if all(s.status == "failed" for s in subtasks):
                test_run.status = "failed"
                test_run.error_message = "All subtasks failed"
            else:
                test_run.status = "completed"
        else:
            test_run.status = "completed"
    else:
        test_run.status = "failed"

    test_run.finished_at = utc_now()
    await db.flush()
    await ws_manager.broadcast_done(test_run_id)


async def stop_test(test_run_id: int):
    """Terminate the currently running subprocess for a test run."""
    process = _running_processes.get(test_run_id)
    if process and process.returncode is None:
        try:
            process.terminate()
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
