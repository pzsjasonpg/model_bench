#!/bin/bash

# 模型性能测试工具 - 综合测试脚本
# 使用方法: ./run_tests.sh [测试类型] [模型URL] [模型名称] [翻译评估模型URL] [翻译评估模型名称]

# 默认配置
TEST_TYPE="${1:-all}"
MODEL_URL="${2:-http://192.168.0.126:30180/v1}"
MODEL_NAME="${3:-Qwen/Qwen3-8B}"
MODEL2_URL="${4:-http://192.168.0.126:30180/v1}"
MODEL2_NAME="${5:-Qwen/Qwen3-8B}"

echo "=========================================="
echo "模型性能测试工具 - 综合测试脚本"
echo "=========================================="
echo "模型URL: $MODEL_URL"
echo "模型名称: $MODEL_NAME"
echo "翻译评估模型URL: $MODEL2_URL"
echo "翻译评估模型名称: $MODEL2_NAME"
echo "测试类型: $TEST_TYPE"
echo "=========================================="

# 基本性能测试
run_basic_test() {
    echo ""
    echo ">>> 运行基本性能测试..."
    # python -m src.main --total 1 --input-tokens 100-8000 --output-tokens 100-8000 --model-type openai --api-key 123 --base-url "http://192.168.0.126:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type random  --ignore-eos
    python -m src.main --total 1 --input-tokens 100-8000 --output-tokens 100-8000 --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  --ignore-eos
}

# 并发测试
run_concurrency_test() {
    echo ""
    echo ">>> 运行并发测试..."
    python -m src.main --total 32 --max-concurrency 8 --input-tokens 100-8000  --output-tokens 100-8000 --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  --ignore-eos
}

# 多轮问答测试
run_multi_round_test() {
    echo ""
    echo ">>> 运行多轮问答测试..."
    python -m src.main --total 1 --max-concurrency 1 --input-tokens 900-1000  --output-tokens 900-1000  --rounds 10 --wait-rounds --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json  --ignore-eos
}

# 摘要场景测试
run_summary_test() {
    echo ""
    echo ">>> 运行摘要场景测试..."
    python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-500 --scenario summary --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json
}

# 翻译场景测试
run_translate_test() {
    echo ""
    echo ">>> 运行翻译场景测试..."
    python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-8000 --scenario translate --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json
}

# 实体抽取场景测试
run_entity_extraction_test() {
    echo ""
    echo ">>> 运行实体抽取场景测试..."
    python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-500 --scenario entity_extraction --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json
}

# 长文档测试
run_long_doc_test() {
    echo ""
    echo ">>> 运行长文档测试..."
    python tests/long_doc_qa.py --num-documents 2 --document-length 5000 --output-len 100 --repeat-count 2  --base-url "${MODEL_URL}" --model "${MODEL_NAME}" --max-inflight-requests 2
}

# 多文档测试
run_multi_doc_test() {
    echo ""
    echo ">>> 运行多文档测试..."
    python tests/multi_doc_qa.py --num-total-documents 2 --document-length 1000 --num-requests 2 --num-docs-per-request 2 --base-url "${MODEL_URL}" --model "${MODEL_NAME}" 
}

# RAG测试
run_rag_test() {
    echo ""
    echo ">>> 运行RAG测试..."
    if [ -f "tests/testrag/test_dataset.json" ]; then
        python tests/testrag/rag.py --qps 1  --dataset tests/testrag/test_dataset.json --prompt-build-method QA --base-url "${MODEL_URL}" --model "${MODEL_NAME}" 
    else
        echo "警告: RAG测试数据集不存在，跳过RAG测试"
    fi
}

# 多语种翻译质量评估测试
run_mtqs_test() {
    echo ""
    echo ">>> 运行多语种翻译质量评估测试..."
    if [ -f "data/mtqs/语种语料V2.xlsx" ]; then
        python tests/mtqs/main-new.py --excel-file data/mtqs/语种语料V2.xlsx --model-a-url  ${MODEL_URL}/chat/completions --model-b-url ${MODEL_URL}/chat/completions  --concurrency 1 --translate-model "${MODEL2_NAME}" --evaluate-model "${MODEL2_NAME}"
    else
        echo "警告: 多语种翻译质量评估测试数据集不存在，跳过该测试"
    fi
}

# 根据测试类型运行相应测试
case "$TEST_TYPE" in
    "basic")
        run_basic_test
        ;;
    "concurrency")
        run_concurrency_test
        ;;
    "multi_round")
        run_multi_round_test
        ;;
    "summary")
        run_summary_test
        ;;
    "translate")
        run_translate_test
        ;;
    "entity")
        run_entity_extraction_test
        ;;
    "long_doc")
        run_long_doc_test
        ;;
    "multi_doc")
        run_multi_doc_test
        ;;
    "rag")
        run_rag_test
        ;;
    "mtqs")
        run_mtqs_test
        ;;
    "all")
        run_basic_test
        run_concurrency_test
        run_multi_round_test
        run_summary_test
        run_translate_test
        run_entity_extraction_test
        run_long_doc_test
        run_multi_doc_test
        run_rag_test
        run_mtqs_test
        ;;
    *)
        echo "未知的测试类型: $TEST_TYPE"
        echo "可用的测试类型: basic, concurrency, multi_round, summary, translate, entity, long_doc, multi_doc, rag, mtqs, all"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="
