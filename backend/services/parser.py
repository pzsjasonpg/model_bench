"""Parse stdout output lines to structured metrics."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Known patterns from src/main.py output (both chat and embedding)
PATTERNS = [
    # Chat patterns
    (re.compile(r"平均TTFT:\s*([\d.]+)毫秒"), "avg_ttft_ms"),
    (re.compile(r"最小TTFT:\s*([\d.]+)毫秒"), "min_ttft_ms"),
    (re.compile(r"最大TTFT:\s*([\d.]+)毫秒"), "max_ttft_ms"),
    (re.compile(r"输入token吞吐率:\s*([\d.]+)"), "input_throughput"),
    (re.compile(r"输出token吞吐率:\s*([\d.]+)"), "output_throughput"),
    (re.compile(r"平均单个请求延迟总时间:\s*([\d.]+)秒"), "avg_total_time_s"),
    (re.compile(r"最小单个请求延迟总时间:\s*([\d.]+)秒"), "min_total_time_s"),
    (re.compile(r"最大单个请求延迟总时间:\s*([\d.]+)秒"), "max_total_time_s"),
    (re.compile(r"所有请求耗时:\s*([\d.]+)秒"), "all_requests_time_s"),
    (re.compile(r"总请求数:\s*(\d+)"), "total_requests"),
    (re.compile(r"成功请求数:\s*(\d+)"), "success_total"),
    (re.compile(r"失败请求数:\s*(\d+)"), "failed_total"),
    (re.compile(r"所有请求输入token总数:\s*([\d.]+)"), "total_input_tokens"),
    (re.compile(r"所有请求输出token总数:\s*([\d.]+)"), "total_output_tokens"),
    (re.compile(r"平均非首token时延:\s*([\d.]+)毫秒"), "avg_non_first_token_latency_ms"),
    (re.compile(r"最小非首token时延:\s*([\d.]+)毫秒"), "min_non_first_token_latency_ms"),
    (re.compile(r"最大非首token时延:\s*([\d.]+)毫秒"), "max_non_first_token_latency_ms"),

    # Embedding patterns
    (re.compile(r"QPS:\s*([\d.]+)"), "qps"),
    (re.compile(r"平均延迟:\s*([\d.]+)s"), "avg_latency_s"),
    (re.compile(r"最小延迟:\s*([\d.]+)s"), "min_latency_s"),
    (re.compile(r"最大延迟:\s*([\d.]+)s"), "max_latency_s"),
    (re.compile(r"P50延迟:\s*([\d.]+)s"), "p50_latency_s"),
    (re.compile(r"P90延迟:\s*([\d.]+)s"), "p90_latency_s"),
    (re.compile(r"P99延迟:\s*([\d.]+)s"), "p99_latency_s"),
    (re.compile(r"总耗时:\s*([\d.]+)秒"), "total_time_s"),

    # General
    (re.compile(r"最大并发数:\s*(\d+)"), "max_concurrency"),
    (re.compile(r"模型名:\s*(.+)"), "model_name"),
    (re.compile(r"输入token数:\s*(.+)"), "input_tokens"),
    (re.compile(r"输出token数:\s*(.+)"), "output_tokens"),
    (re.compile(r"平均输入token数:\s*([\d.]+)"), "avg_input_tokens"),
    (re.compile(r"总输入token数:\s*([\d.]+)"), "total_input_tokens_emb"),
]

# Failure-indicating patterns
FAILURE_PATTERNS = [
    re.compile(r"错误:", re.IGNORECASE),
    re.compile(r"Error", re.IGNORECASE),
    re.compile(r"Exception", re.IGNORECASE),
    re.compile(r"Traceback", re.IGNORECASE),
    re.compile(r"失败:", re.IGNORECASE),
    re.compile(r"失败请求数:\s*(?!0\b)\d+", re.IGNORECASE),
    re.compile(r"Failed:", re.IGNORECASE),
]


def parse_metrics(lines: List[str]) -> Dict[str, Any]:
    """Parse a list of stdout lines into a structured metrics dict.

    Returns a dict with keys like: avg_ttft_ms, input_throughput, etc.
    All numeric values are converted to float/int.
    """
    metrics: Dict[str, Any] = {}
    errors: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for failure indicators
        for pat in FAILURE_PATTERNS:
            if pat.search(stripped):
                errors.append(stripped)
                break

        # Match known metrics
        for pat, key in PATTERNS:
            m = pat.search(stripped)
            if m:
                val = m.group(1).strip()
                try:
                    if "." in val:
                        metrics[key] = float(val)
                    else:
                        metrics[key] = int(val)
                except ValueError:
                    metrics[key] = val

    metrics["_errors"] = errors
    metrics["_has_errors"] = len(errors) > 0

    return metrics


def parse_aggregated(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate multiple subtask metrics into a summary.

    Returns a dict with:
    - subtask_results: list of per-subtask metrics
    - summary: dict with best/worst for key metrics
    """
    if not metrics_list:
        return {"subtask_results": [], "summary": {}}

    summary: Dict[str, Any] = {}
    numeric_keys = [
        "avg_ttft_ms", "min_ttft_ms", "max_ttft_ms",
        "input_throughput", "output_throughput",
        "avg_total_time_s", "min_total_time_s", "max_total_time_s",
        "all_requests_time_s", "total_requests", "success_total", "failed_total",
        "qps", "avg_latency_s", "p50_latency_s", "p90_latency_s", "p99_latency_s",
        "total_time_s",
    ]

    for key in numeric_keys:
        values = []
        for m in metrics_list:
            v = m.get(key)
            if v is not None and isinstance(v, (int, float)):
                values.append(v)
        if values:
            summary[f"{key}_best"] = max(values)
            summary[f"{key}_worst"] = min(values)
            summary[f"{key}_avg"] = sum(values) / len(values)

    # Count errors
    total_errors = sum(len(m.get("_errors", [])) for m in metrics_list)
    summary["total_errors"] = total_errors
    summary["subtask_count"] = len(metrics_list)

    return {
        "subtask_results": metrics_list,
        "summary": summary,
    }
