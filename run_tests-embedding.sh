#!/bin/bash

# 模型性能测试工具 - 综合测试脚本
# 使用方法: ./run_tests.sh [测试类型] [模型URL] [模型名称] [翻译评估模型URL] [翻译评估模型名称]

# 默认配置
TEST_TYPE="${1:-all}"
MODEL_URL="${2:-http://192.168.0.126:30180/v1}"
MODEL_NAME="${3:-Qwen3-VL-Embedding-2B}"
MODEL2_URL="${4:-http://192.168.0.126:30180/v1}"
MODEL2_NAME="${5:-Qwen3-VL-Embedding-2B}"

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
    python -m src.main --mode embedding --total 1 --max-concurrency 1 --input-tokens 100-500  --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
}

# 并发测试
run_concurrency_test() {
    echo ""
    echo ">>> 运行并发测试..."
    content_length="10-50"
    python -m src.main --mode embedding --total 64 --max-concurrency 1 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 2 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 4 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 8 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 16 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 24 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 32 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 40 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 48 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 56 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 64 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
}

# 短文本并发测试
run_short_text_concurrency_test() {
    echo ""
    echo ">>> 运行并发测试..."
    content_length="10-50"
    python -m src.main --mode embedding --total 64 --max-concurrency 1 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 2 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 4 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 8 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 16 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 24 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 32 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 40 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 48 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 56 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 64 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
}

# 中等长度文本并发测试
run_medium_text_concurrency_test() {
    echo ""
    echo ">>> 运行并发测试..."
    content_length="100-200"
    python -m src.main --mode embedding --total 64 --max-concurrency 1 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 2 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 4 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 8 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 16 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 24 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 32 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 40 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 48 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 56 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 64 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
}

# 长文本并发测试
run_long_text_concurrency_test() {
    echo ""
    echo ">>> 运行并发测试..."
    content_length="500-1000"
    python -m src.main --mode embedding --total 64 --max-concurrency 1 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 2 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 4 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 8 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 16 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 24 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 32 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 40 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 48 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 56 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
    python -m src.main --mode embedding --total 64 --max-concurrency 64 --input-tokens $content_length --model-type openai --api-key 123 --base-url "${MODEL_URL}/chat/completions" --model "${MODEL_NAME}" --input-data-type random  
}


# 根据测试类型运行相应测试
case "$TEST_TYPE" in
    "basic")
        run_basic_test
        ;;
    "concurrency")
        run_concurrency_test
        ;;
    "short")
        run_short_text_concurrency_test
        ;;
    "medium")
        run_medium_text_concurrency_test
        ;;
    "long")
        run_long_text_concurrency_test
        ;;
    "all")
        run_basic_test
        run_concurrency_test
        run_short_text_concurrency_test
        run_medium_text_concurrency_test
        run_long_text_concurrency_test
        ;;
    *)
        echo "未知的测试类型: $TEST_TYPE"
        echo "可用的测试类型: basic, concurrency, short, medium, long, all"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "测试完成!"
echo "=========================================="