"""Test CRUD + run/stop endpoints."""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_session
from ..models import (
    CreateTestRequest,
    LogLine,
    PaginatedResponse,
    SubTask,
    SubTaskOut,
    TestRun,
    TestRunDetailOut,
    TestRunOut,
    utc_now,
)
from ..services.params import (
    TEST_TYPES,
    get_test_type,
    get_default_fixed_params,
    get_default_sweep_key,
    get_default_sweep_values,
)
from ..services.runner import run_test, stop_test
from ..services.parser import parse_aggregated

router = APIRouter(prefix="/api/tests", tags=["tests"])


# ── Helpers ──────────────────────────────────────────────────────────

def _orm_to_out(tr: TestRun) -> TestRunOut:
    return TestRunOut(
        id=tr.id,
        name=tr.name,
        test_type=tr.test_type,
        status=tr.status,
        fixed_params=tr.fixed_params,
        sweep_params=tr.sweep_params,
        sweep_key=tr.sweep_key,
        sweep_values=tr.sweep_values,
        num_subtasks=tr.num_subtasks,
        completed_subtasks=tr.completed_subtasks,
        error_message=tr.error_message,
        created_at=tr.created_at,
        started_at=tr.started_at,
        finished_at=tr.finished_at,
    )


def _subtask_to_out(st: SubTask) -> SubTaskOut:
    return SubTaskOut(
        id=st.id,
        test_run_id=st.test_run_id,
        seq=st.seq,
        status=st.status,
        params=st.params,
        command=st.command,
        pid=st.pid,
        started_at=st.started_at,
        finished_at=st.finished_at,
        result=st.result,
    )


def _build_name(test_type: str, sweep_key: Optional[str], sweep_values: Optional[List[Any]]) -> str:
    """Auto-generate a name if none provided."""
    info = get_test_type(test_type)
    label = info["label"] if info else test_type
    if sweep_key and sweep_values:
        return f"{label} ({sweep_key}: {sweep_values})"
    return label


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("", response_model=TestRunOut, status_code=201)
async def create_test(
    req: CreateTestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    """Create a new test run and start executing it."""
    # Validate test_type
    info = get_test_type(req.test_type)
    if not info:
        raise HTTPException(status_code=400, detail=f"Unknown test type: {req.test_type}")

    # Merge fixed_params with template defaults
    defaults = get_default_fixed_params(req.test_type)
    merged_fixed: Dict[str, Any] = {**defaults, **req.fixed_params}

    # Determine sweep
    sweep_key = req.sweep_key or get_default_sweep_key(req.test_type)
    sweep_values = req.sweep_values or get_default_sweep_values(req.test_type)

    # Build sweep params if applicable
    sweep_params_dict = None
    if sweep_key and sweep_values:
        sweep_params_dict = {
            "key": sweep_key,
            "label": sweep_key,
            "values": sweep_values,
        }

    num_subtasks = len(sweep_values) if sweep_values else 1

    # Generate name
    name = req.name or _build_name(req.test_type, sweep_key, sweep_values)

    # Create TestRun
    test_run = TestRun(
        name=name,
        test_type=req.test_type,
        status="pending",
        fixed_params=json.dumps(merged_fixed, ensure_ascii=False),
        sweep_params=json.dumps(sweep_params_dict, ensure_ascii=False) if sweep_params_dict else None,
        sweep_key=sweep_key,
        sweep_values=json.dumps(sweep_values, ensure_ascii=False) if sweep_values else None,
        num_subtasks=num_subtasks,
        completed_subtasks=0,
        created_at=utc_now(),
    )
    db.add(test_run)
    await db.flush()
    await db.refresh(test_run)

    # Create SubTasks
    if sweep_values:
        for idx, sv in enumerate(sweep_values):
            subtask_params = {**merged_fixed, sweep_key: sv}
            # Build preliminary command (will be updated when running)
            cmd = json.dumps(subtask_params, ensure_ascii=False)
            subtask = SubTask(
                test_run_id=test_run.id,
                seq=idx + 1,
                status="pending",
                params=json.dumps(subtask_params, ensure_ascii=False),
                command=cmd,
            )
            db.add(subtask)
    else:
        subtask = SubTask(
            test_run_id=test_run.id,
            seq=1,
            status="pending",
            params=json.dumps(merged_fixed, ensure_ascii=False),
            command=json.dumps(merged_fixed, ensure_ascii=False),
        )
        db.add(subtask)

    await db.flush()
    await db.commit()

    # Start running in background
    background_tasks.add_task(_run_test_safe, test_run.id)

    return _orm_to_out(test_run)


async def _run_test_safe(test_run_id: int):
    """Wrapper that catches exceptions during test execution."""
    from ..db import async_session_factory
    from ..models import TestRun as TR, utc_now as now

    logger = logging.getLogger(__name__)
    logger.info(f"Background task started for test_run_id={test_run_id}")
    async with async_session_factory() as session:
        try:
            await run_test(test_run_id, session)
            await session.commit()
            logger.info(f"Background task completed for test_run_id={test_run_id}")
        except Exception as e:
            logger.exception(f"Background task failed for test_run_id={test_run_id}: {e}")
            await session.rollback()
            # Try to update status to failed
            try:
                result = await session.execute(select(TR).where(TR.id == test_run_id))
                tr = result.scalar_one_or_none()
                if tr:
                    tr.status = "failed"
                    tr.error_message = str(e)
                    tr.finished_at = now()
                    await session.commit()
            except Exception:
                pass


@router.get("", response_model=PaginatedResponse)
async def list_tests(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    """List test runs with optional status filter and pagination."""
    # Count total
    count_q = select(func.count(TestRun.id))
    if status:
        count_q = count_q.where(TestRun.status == status)
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    # Fetch page
    q = select(TestRun).order_by(TestRun.created_at.desc())
    if status:
        q = q.where(TestRun.status == status)
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    runs = result.scalars().all()

    return PaginatedResponse(
        items=[_orm_to_out(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.get("/{test_id}", response_model=TestRunDetailOut)
async def get_test(
    test_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Get a single test run with all subtasks."""
    result = await db.execute(
        select(TestRun)
        .where(TestRun.id == test_id)
        .options(selectinload(TestRun.subtasks))
    )
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Test run not found")

    out = TestRunDetailOut(
        id=tr.id,
        name=tr.name,
        test_type=tr.test_type,
        status=tr.status,
        fixed_params=tr.fixed_params,
        sweep_params=tr.sweep_params,
        sweep_key=tr.sweep_key,
        sweep_values=tr.sweep_values,
        num_subtasks=tr.num_subtasks,
        completed_subtasks=tr.completed_subtasks,
        error_message=tr.error_message,
        created_at=tr.created_at,
        started_at=tr.started_at,
        finished_at=tr.finished_at,
        subtasks=[_subtask_to_out(st) for st in (tr.subtasks or [])],
    )
    return out


@router.post("/{test_id}/stop")
async def stop_test_endpoint(
    test_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Stop a running test."""
    result = await db.execute(select(TestRun).where(TestRun.id == test_id))
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Test run not found")

    if tr.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail=f"Cannot stop test in status: {tr.status}")

    await stop_test(test_id)

    tr.status = "stopped"
    tr.finished_at = utc_now()
    await db.flush()

    # Also mark any pending/running subtasks as stopped
    sub_result = await db.execute(
        select(SubTask).where(
            SubTask.test_run_id == test_id,
            SubTask.status.in_(["pending", "running"]),
        )
    )
    for st in sub_result.scalars().all():
        st.status = "stopped"
        st.finished_at = st.finished_at or utc_now()
    await db.flush()

    return {"message": "Test stopped", "id": test_id}


@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Delete a test run and all associated data."""
    result = await db.execute(select(TestRun).where(TestRun.id == test_id))
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Stop if running
    if tr.status == "running":
        await stop_test(test_id)

    # Delete log lines, subtasks, and test run
    await db.execute(delete(LogLine).where(LogLine.test_run_id == test_id))
    await db.execute(delete(SubTask).where(SubTask.test_run_id == test_id))
    await db.execute(delete(TestRun).where(TestRun.id == test_id))
    await db.flush()

    return {"message": "Test deleted", "id": test_id}


@router.get("/{test_id}/logs")
async def get_test_logs(
    test_id: int,
    subtask_id: Optional[int] = Query(default=None),
    after_timestamp: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    db: AsyncSession = Depends(get_session),
):
    """Get log lines for a test run."""
    # Verify test exists
    result = await db.execute(select(TestRun.id).where(TestRun.id == test_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Test run not found")

    q = select(LogLine).where(LogLine.test_run_id == test_id)
    if subtask_id is not None:
        q = q.where(LogLine.subtask_id == subtask_id)
    if after_timestamp:
        q = q.where(LogLine.timestamp > after_timestamp)
    q = q.order_by(LogLine.id.asc()).limit(limit)

    result = await db.execute(q)
    lines = result.scalars().all()

    return [
        {
            "id": l.id,
            "test_run_id": l.test_run_id,
            "subtask_id": l.subtask_id,
            "line": l.line,
            "timestamp": l.timestamp,
        }
        for l in lines
    ]


@router.get("/{test_id}/result")
async def get_test_result(
    test_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Get aggregated result for a test run."""
    result = await db.execute(
        select(TestRun)
        .where(TestRun.id == test_id)
        .options(selectinload(TestRun.subtasks))
    )
    tr = result.scalar_one_or_none()
    if not tr:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Collect per-subtask results
    metrics_list = []
    for st in (tr.subtasks or []):
        if st.result:
            try:
                parsed = json.loads(st.result)
                # Clean internal keys
                clean = {k: v for k, v in parsed.items() if not k.startswith("_")}
                clean["_seq"] = st.seq
                clean["_status"] = st.status
                clean["_sweep_value"] = json.loads(st.params).get(tr.sweep_key) if tr.sweep_key else None
                metrics_list.append(clean)
            except (json.JSONDecodeError, TypeError):
                pass

    aggregated = parse_aggregated([m for m in metrics_list if not isinstance(m, str)])

    return {
        "test_id": test_id,
        "name": tr.name,
        "test_type": tr.test_type,
        "status": tr.status,
        "sweep_key": tr.sweep_key,
        "aggregated": aggregated,
    }
