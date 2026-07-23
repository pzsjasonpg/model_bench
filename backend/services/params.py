"""Parameter templates and defaults for all 15 test types."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# ── Common model connection params (used by most chat types) ──────────
COMMON_MODEL_PARAMS: List[Dict[str, Any]] = [
    {"key": "model_type", "label": "模型类型", "type": "select", "options": ["mock", "openai", "local"], "default": "openai"},
    {"key": "api_key", "label": "API密钥", "type": "string", "default": "123"},
    {"key": "model", "label": "模型名称", "type": "string", "default": "Qwen/Qwen3-8B"},
    {"key": "base_url", "label": "API地址", "type": "string", "default": "http://192.168.0.126:8000/v1"},
    {"key": "enable_thinking", "label": "开启思考模式", "type": "bool", "default": False},
]

COMMON_CHAT_PARAMS: List[Dict[str, Any]] = [
    {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
    {"key": "ignore_eos", "label": "忽略EOS", "type": "bool", "default": True},
]

CHAT_SWEEP_DEFAULTS = {
    "max_concurrency": {"key": "max_concurrency", "label": "最大并发数", "defaults": [2, 4, 8]},
}
EMBED_SWEEP_DEFAULTS = {
    "max_concurrency": {"key": "max_concurrency", "label": "最大并发数", "defaults": [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64]},
}
LONG_DOC_SWEEP_DEFAULTS = {
    "max_inflight_requests": {"key": "max_inflight_requests", "label": "最大并发请求数", "defaults": [2, 4, 8]},
}


# ── All 15 test types ────────────────────────────────────────────────

TEST_TYPES: List[Dict[str, Any]] = [
    # ── Chat types (src.main) ──────────────────────────────────────
    {
        "type": "basic",
        "category": "chat",
        "label": "基本性能测试",
        "description": "单次请求测试，评估模型基础性能指标（TTFT、吞吐率、延迟等）",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + COMMON_CHAT_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 1},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "100-8000"},
            {"key": "output_tokens", "label": "输出Token数", "type": "string", "default": "100-8000"},
        ],
        "sweep_config": None,
        "default_fixed": {
            "total": 1, "input_tokens": "100-8000", "output_tokens": "100-8000",
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "random", "ignore_eos": True, "enable_thinking": False,
        },
    },
    {
        "type": "concurrency",
        "category": "chat",
        "label": "并发测试",
        "description": "固定Token长度下的并发测试，评估模型在不同并发数下的吞吐和延迟",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + COMMON_CHAT_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 48},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "1000"},
            {"key": "output_tokens", "label": "输出Token数", "type": "string", "default": "1000"},
        ],
        "sweep_config": CHAT_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 48, "input_tokens": "1000", "output_tokens": "1000",
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "random", "ignore_eos": True, "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "multi_round",
        "category": "chat",
        "label": "多轮问答测试",
        "description": "多轮对话性能测试，评估模型在多轮交互场景下的表现",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + COMMON_CHAT_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 48},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "800"},
            {"key": "output_tokens", "label": "输出Token数", "type": "string", "default": "800"},
            {"key": "rounds", "label": "对话轮数", "type": "number", "default": 3},
            {"key": "wait_rounds", "label": "等待轮次", "type": "bool", "default": True},
            {"key": "custom_data_path", "label": "自定义数据路径", "type": "string",
             "default": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json"},
        ],
        "sweep_config": CHAT_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 48, "input_tokens": "800", "output_tokens": "800",
            "rounds": 3, "wait_rounds": True,
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "custom",
            "custom_data_path": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json",
            "ignore_eos": True, "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "summary",
        "category": "chat",
        "label": "摘要场景测试",
        "description": "长文本摘要场景性能测试，模拟摘要生成的实际使用情况",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 48},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "1000-10000"},
            {"key": "output_tokens", "label": "输出Token数", "type": "string", "default": "100-500"},
            {"key": "scenario", "label": "场景", "type": "fixed", "default": "summary"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "custom"},
            {"key": "custom_data_path", "label": "自定义数据路径", "type": "string",
             "default": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json"},
        ],
        "sweep_config": CHAT_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 48, "input_tokens": "1000-10000", "output_tokens": "100-500",
            "scenario": "summary",
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "custom",
            "custom_data_path": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json",
            "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "translate",
        "category": "chat",
        "label": "翻译场景测试",
        "description": "翻译场景性能测试，评估模型在翻译任务中的表现",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 48},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "100-5000"},
            {"key": "scenario", "label": "场景", "type": "fixed", "default": "translate"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "custom"},
            {"key": "custom_data_path", "label": "自定义数据路径", "type": "string",
             "default": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json"},
        ],
        "sweep_config": CHAT_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 48, "input_tokens": "100-5000",
            "scenario": "translate",
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "custom",
            "custom_data_path": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json",
            "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "entity",
        "category": "chat",
        "label": "实体抽取测试",
        "description": "实体抽取场景性能测试，评估模型在信息抽取任务中的表现",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 48},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "1000-10000"},
            {"key": "output_tokens", "label": "输出Token数", "type": "string", "default": "100-500"},
            {"key": "scenario", "label": "场景", "type": "fixed", "default": "entity_extraction"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "custom"},
            {"key": "custom_data_path", "label": "自定义数据路径", "type": "string",
             "default": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json"},
        ],
        "sweep_config": CHAT_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 48, "input_tokens": "1000-10000", "output_tokens": "100-500",
            "scenario": "entity_extraction",
            "model_type": "openai", "api_key": "123", "model": "Qwen/Qwen3-8B",
            "base_url": "http://192.168.0.126:8000/v1",
            "input_data_type": "custom",
            "custom_data_path": "data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json",
            "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [2, 4, 8],
    },

    # ── Chat types (tests/*.py) ─────────────────────────────────────
    {
        "type": "long_doc",
        "category": "chat",
        "label": "长文档测试",
        "description": "长文档问答性能测试，评估模型处理超长文档的能力",
        "script": "tests/long_doc_qa.py",
        "fixed_params": [
            {"key": "base_url", "label": "API地址", "type": "string", "default": "http://192.168.0.126:8000/v1"},
            {"key": "model", "label": "模型名称", "type": "string", "default": "Qwen/Qwen3-8B"},
            {"key": "num_documents", "label": "文档数", "type": "number", "default": 48},
            {"key": "document_length", "label": "文档长度(tokens)", "type": "number", "default": 10000},
            {"key": "output_len", "label": "输出长度", "type": "number", "default": 100},
            {"key": "repeat_count", "label": "重复次数", "type": "number", "default": 1},
        ],
        "sweep_config": LONG_DOC_SWEEP_DEFAULTS["max_inflight_requests"],
        "default_fixed": {
            "base_url": "http://192.168.0.126:8000/v1",
            "model": "Qwen/Qwen3-8B",
            "num_documents": 48, "document_length": 10000,
            "output_len": 100, "repeat_count": 1,
        },
        "default_sweep_key": "max_inflight_requests",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "multi_doc",
        "category": "chat",
        "label": "多文档测试",
        "description": "多文档问答性能测试，评估模型同时处理多个文档的能力",
        "script": "tests/multi_doc_qa.py",
        "fixed_params": [
            {"key": "base_url", "label": "API地址", "type": "string", "default": "http://192.168.0.126:8000/v1"},
            {"key": "model", "label": "模型名称", "type": "string", "default": "Qwen/Qwen3-8B"},
            {"key": "num_total_documents", "label": "总文档数", "type": "number", "default": 48},
            {"key": "document_length", "label": "文档长度(tokens)", "type": "number", "default": 8000},
            {"key": "num_requests", "label": "请求数", "type": "number", "default": 48},
            {"key": "num_docs_per_request", "label": "每请求文档数", "type": "number", "default": 2},
        ],
        "sweep_config": LONG_DOC_SWEEP_DEFAULTS["max_inflight_requests"],
        "default_fixed": {
            "base_url": "http://192.168.0.126:8000/v1",
            "model": "Qwen/Qwen3-8B",
            "num_total_documents": 48, "document_length": 8000,
            "num_requests": 48, "num_docs_per_request": 2,
        },
        "default_sweep_key": "max_inflight_requests",
        "default_sweep_values": [2, 4, 8],
    },
    {
        "type": "rag",
        "category": "chat",
        "label": "RAG测试",
        "description": "RAG管道的性能测试，评估模型在检索增强生成场景中的表现",
        "script": "tests/testrag/rag.py",
        "fixed_params": [
            {"key": "base_url", "label": "API地址", "type": "string", "default": "http://192.168.0.126:8000/v1"},
            {"key": "model", "label": "模型名称", "type": "string", "default": "Qwen/Qwen3-8B"},
            {"key": "qps", "label": "QPS", "type": "number", "default": 2},
            {"key": "dataset", "label": "数据集路径", "type": "string", "default": "tests/testrag/musique_s.json"},
            {"key": "prompt_build_method", "label": "Prompt构建方法", "type": "select", "options": ["QA", "FEW_SHOT"], "default": "QA"},
        ],
        "sweep_config": None,
        "default_fixed": {
            "base_url": "http://192.168.0.126:8000/v1",
            "model": "Qwen/Qwen3-8B",
            "qps": 2,
            "dataset": "tests/testrag/musique_s.json",
            "prompt_build_method": "QA",
        },
    },
    {
        "type": "mtqs",
        "category": "chat",
        "label": "多语种翻译质量测试",
        "description": "多语种翻译质量评估，测试翻译和评估模型的综合能力",
        "script": "tests/mtqs/main-new.py",
        "fixed_params": [
            {"key": "model_a_url", "label": "翻译模型URL", "type": "string", "default": "http://192.168.0.126:8000/v1"},
            {"key": "model_b_url", "label": "评估模型URL", "type": "string", "default": "http://192.168.0.126:8000/v1"},
            {"key": "translate_model", "label": "翻译模型名", "type": "string", "default": "Qwen/Qwen3-8B"},
            {"key": "evaluate_model", "label": "评估模型名", "type": "string", "default": "Qwen/Qwen3-8B"},
            {"key": "excel_file", "label": "Excel文件路径", "type": "string", "default": "data/mtqs/语种语料V2.xlsx"},
            {"key": "concurrency", "label": "并发数", "type": "number", "default": 1},
        ],
        "sweep_config": None,
        "default_fixed": {
            "model_a_url": "http://192.168.0.126:8000/v1",
            "model_b_url": "http://192.168.0.126:8000/v1",
            "translate_model": "Qwen/Qwen3-8B",
            "evaluate_model": "Qwen/Qwen3-8B",
            "excel_file": "data/mtqs/语种语料V2.xlsx",
            "concurrency": 1,
        },
    },

    # ── Embedding types ─────────────────────────────────────────────
    {
        "type": "embed_basic",
        "category": "embedding",
        "label": "Embedding基本测试",
        "description": "Embedding模型基本性能测试，单次请求评估基础指标",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 1},
            {"key": "max_concurrency", "label": "最大并发数", "type": "number", "default": 1},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "100-500"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
        ],
        "sweep_config": None,
        "default_fixed": {
            "total": 1, "max_concurrency": 1, "input_tokens": "100-500",
            "model_type": "openai", "api_key": "123", "model": "bge-m3-cpu",
            "base_url": "http://192.168.0.126:30180/v1",
            "input_data_type": "random", "enable_thinking": False,
        },
    },
    {
        "type": "embed_concurrency",
        "category": "embedding",
        "label": "Embedding并发测试",
        "description": "Embedding模型并发性能测试，短文本下的并发吞吐评估",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 64},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "10-50"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
        ],
        "sweep_config": EMBED_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 64, "input_tokens": "10-50",
            "model_type": "openai", "api_key": "123", "model": "bge-m3-cpu",
            "base_url": "http://192.168.0.126:30180/v1",
            "input_data_type": "random", "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64],
    },
    {
        "type": "embed_short",
        "category": "embedding",
        "label": "Embedding短文本并发",
        "description": "短文本Embedding并发测试（10-50 tokens），评估小文本下的性能",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 64},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "10-50"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
        ],
        "sweep_config": EMBED_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 64, "input_tokens": "10-50",
            "model_type": "openai", "api_key": "123", "model": "bge-m3-cpu",
            "base_url": "http://192.168.0.126:30180/v1",
            "input_data_type": "random", "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64],
    },
    {
        "type": "embed_medium",
        "category": "embedding",
        "label": "Embedding中文本并发",
        "description": "中等文本Embedding并发测试（100-200 tokens），评估中等长度文本的性能",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 64},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "100-200"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
        ],
        "sweep_config": EMBED_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 64, "input_tokens": "100-200",
            "model_type": "openai", "api_key": "123", "model": "bge-m3-cpu",
            "base_url": "http://192.168.0.126:30180/v1",
            "input_data_type": "random", "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64],
    },
    {
        "type": "embed_long",
        "category": "embedding",
        "label": "Embedding长文本并发",
        "description": "长文本Embedding并发测试（500-1000 tokens），评估长文本下的性能",
        "script": "src.main",
        "fixed_params": COMMON_MODEL_PARAMS + [
            {"key": "total", "label": "总请求数", "type": "number", "default": 64},
            {"key": "input_tokens", "label": "输入Token数", "type": "string", "default": "500-1000"},
            {"key": "input_data_type", "label": "输入数据类型", "type": "select", "options": ["random", "custom"], "default": "random"},
        ],
        "sweep_config": EMBED_SWEEP_DEFAULTS["max_concurrency"],
        "default_fixed": {
            "total": 64, "input_tokens": "500-1000",
            "model_type": "openai", "api_key": "123", "model": "bge-m3-cpu",
            "base_url": "http://192.168.0.126:30180/v1",
            "input_data_type": "random", "enable_thinking": False,
        },
        "default_sweep_key": "max_concurrency",
        "default_sweep_values": [1, 2, 4, 8, 16, 24, 32, 40, 48, 56, 64],
    },
]


def get_test_type(ty: str) -> Optional[Dict[str, Any]]:
    """Look up a test type by its identifier."""
    for t in TEST_TYPES:
        if t["type"] == ty:
            return t
    return None


def get_default_fixed_params(ty: str) -> Dict[str, Any]:
    """Get the default fixed params dict for a test type."""
    info = get_test_type(ty)
    if info and "default_fixed" in info:
        return dict(info["default_fixed"])
    return {}


def get_default_sweep_key(ty: str) -> Optional[str]:
    """Get the default sweep key for a test type."""
    info = get_test_type(ty)
    return info.get("default_sweep_key") if info else None


def get_default_sweep_values(ty: str) -> List[Any]:
    """Get the default sweep values for a test type."""
    info = get_test_type(ty)
    return list(info.get("default_sweep_values", [])) if info else []
