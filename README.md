# 模型性能测试工具

这是一个用于测试大语言模型性能的Python工具，支持设置总请求数、最大并发数、输入token数、输出token数，并能计算TTFT、输入token吞吐率、单个请求延迟总时间、所有请求耗时和缓存命中率等指标。

## 功能特点

- 支持设置总请求数和最大并发数
- 支持控制输入token数和输出token数
- 计算多种性能指标：
  - TTFT (Time To First Token)：首token响应时间
  - 输入token吞吐率：tokens/秒
  - 单个请求延迟总时间
  - 所有请求耗时
  - 缓存命中率
- 支持多种模型接口：
  - OpenAI API
  - 本地模型
  - 模拟模型（用于测试）
- 支持流式响应
- 实时显示测试进度和缓存命中情况
- 支持生成多种格式的测试报告：
  - 文本格式
  - JSON格式
  - CSV格式
- 支持多轮问答测试（设置轮次和轮次等待模式）
- 支持自定义数据输入（从JSON文件加载测试数据）
- 支持多种查询场景：
  - 摘要场景（生成文本摘要）
  - 翻译场景（文本翻译）
  - 实体抽取场景（提取人员信息）
- 支持思考模式控制（启用/禁用模型思考过程）

## 安装方法

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd model_bench
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

3. **激活虚拟环境**
   - Windows:
     ```bash
     .\venv\Scripts\Activate.ps1
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 测试脚本

我们提供了综合测试脚本 `run_tests.sh`，可以一键运行多种测试场景：

```bash
# 运行所有测试
./run_tests.sh

# 运行指定类型的测试
./run_tests.sh concurrency  # 运行并发测试

# 运行指定模型的测试
./run_tests.sh basic http://localhost:30180/v1 gpt-3.5-turbo
```

### 基本用法

```bash
python -m src.main --total 32 --max-concurrency 8 --input-tokens 100-8000  --output-tokens 100-8000 --model-type openai --api-key 123 --base-url "http://localhost:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type random  --ignore-eos
```

#### 测试指定模型

```bash
# 测试OpenAI模型
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type openai --api-key your_api_key

# 测试本地模型
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type local --model-path ./model

# 测试指定模型地址
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type openai --api-key test_key --base-url http://localhost:8000/v1/chat/completions --model gpt-3.5-turbo
```

#### 使用最大并发数限制

```bash
# 总请求数为5，但最大并发数为2（分批执行）
python -m src.main --total 5 --max-concurrency 2 --input-tokens 100 --output-tokens 50
```

#### 使用忽略EOS参数

```bash
# 测试时忽略EOS token，不截断输出
python -m src.main --total 10 --max-concurrency 3 --input-tokens 150 --output-tokens 100 --ignore-eos
```
#### 使用自定义数据

```bash
# 使用自定义数据文件
python -m src.main --total 5 --max-concurrency 2 --input-tokens 100 --output-tokens 100 --input-data-type custom --custom-data-path path/to/data.json
```

#### 控制思考模式

```bash
# 启用思考模式
python -m src.main --total 1 --max-concurrency 1 --input-tokens 100 --output-tokens 100 --enable-thinking
```

#### 生成测试报告

```bash
# 生成JSON格式报告
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --report-format json --output-file report.json

# 生成CSV格式报告
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --report-format csv --output-file report.csv
```


### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--total` | int | 1 | 总请求的条数 |
| `--max-concurrency` | int | None | 最大并发数（限制实际并发执行的请求数） |
| `--input-tokens` | str | 100 | 输入token数（可以是范围，如"100-200"） |
| `--output-tokens` | str | 100 | 输出token数（可以是范围，如"100-200"） |
| `--ignore-eos` | bool | False | 忽略EOS token，不截断输出 |
| `--rounds` | int | 0 | 多轮问答次数，大于0时启用多轮问答 |
| `--wait-rounds` | bool | False | 多轮对话时，等待当前轮次所有请求完成后再开始下一轮 |
| `--input-data-type` | str | random | 输入数据类型：random（随机生成数据）或custom（自定义数据） |
| `--custom-data-path` | str | None | 自定义数据文件路径，当input-data-type为custom时使用 |
| `--scenario` | str | None | 查询场景参数：summary（摘要场景）、translate（翻译场景）、entity_extraction（实体抽取场景） |
| `--enable-thinking` | bool | False | 开启思考模式，默认不开启 |
| `--model-type` | str | mock | 模型类型（mock/openai/local） |
| `--api-key` | str | None | OpenAI API密钥 |
| `--model` | str | gpt-3.5-turbo | 模型名称 |
| `--model-path` | str | None | 本地模型路径 |
| `--base-url` | str | None | 模型请求地址 |
| `--command` | str | python | 本地模型命令名 |
| `--report-format` | str | text | 报告格式（text/json/csv） |
| `--output-file` | str | None | 报告输出文件路径 |


### 多轮问答测试

```bash
# 启用多轮问答，设置10轮，等待轮次模式
python -m src.main --total 1 --max-concurrency 1 --input-tokens 900-1000  --output-tokens 900-1000  --rounds 10 --wait-rounds --model-type openai --api-key 123 --base-url "http://192.168.0.126:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type custom --custom-data-path data\translate\datasets--SynthData--Improved_Chinese_to_English\snapshots\8d8328934140218285221d9fe23fe0f6e7a2df96\btranslate.json  --ignore-eos
```


### 使用查询场景

```bash
# 使用摘要场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-500 --scenario summary --model-type openai --api-key 123 --base-url "http://192.168.0.126:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json

# 使用翻译场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-8000 --scenario translate --model-type openai --api-key 123 --base-url "http://192.168.0.126:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json

# 使用实体抽取场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 100-8000 --output-tokens 100-500 --scenario entity_extraction --model-type openai --api-key 123 --base-url "http://192.168.0.126:30180/v1/chat/completions" --model "Qwen/Qwen3-8B" --input-data-type custom --custom-data-path data/translate/datasets--SynthData--Improved_Chinese_to_English/snapshots/8d8328934140218285221d9fe23fe0f6e7a2df96/btranslate.json
```


### 长文档测试

长文档测试用于评估模型处理长文档的性能，特别关注缓存机制对性能的影响。

#### 安装额外依赖

```bash
pip install openai
```

#### 运行长文档测试

```bash
# 基本长文档测试（2个文档，每个5000tokens，2次重复）
python tests/long_doc_qa.py --num-documents 2 --document-length 5000 --output-len 100 --repeat-count 2  --base-url "http://192.168.0.126:30180/v1" --model "Qwen/Qwen3-8B" --max-inflight-requests 2
```

#### 长文档测试参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--num-documents` | int | 8 | 测试文档数量 |
| `--document-length` | int | 20000 | 每个文档的长度（tokens） |
| `--output-len` | int | 100 | 每个prompt的输出token数 |
| `--repeat-count` | int | 2 | 每个prompt的重复次数 |
| `--repeat-mode` | str | random | 重复模式（random/tile/interleave） |
| `--max-inflight-requests` | int | 2 | 最大并发请求数 |
| `--hit-miss-ratio` | str | None | 缓存命中/未命中比例（如3:1） |
| `--visualize` | bool | False | 可视化测试结果 |

### 多文档测试

多文档测试用于评估模型处理多个文档的性能，特别关注模型在处理包含多个文档的请求时的表现。

#### 安装额外依赖

```bash
pip install openai
```

#### 运行多文档测试

```bash
# 基本多文档测试（2个总文档，每个1000tokens，2个请求，每个请求2个文档）
python tests/multi_doc_qa.py --num-total-documents 2 --document-length 1000 --num-requests 2 --num-docs-per-request 2 --base-url "http://192.168.0.126:30180/v1" --model "Qwen/Qwen3-8B" 
```

#### 多文档测试参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--num-total-documents` | int | 100 | 总文档数量 |
| `--document-length` | int | 3000 | 每个文档的长度（tokens） |
| `--num-requests` | int | 100 | 发送的请求数量 |
| `--num-docs-per-request` | int | 5 | 每个请求包含的文档数量 |
| `--max-inflight-requests` | int | 20 | 最大并发请求数 |
| `--base-url` | str | None | 模型请求地址（与--port互斥） |
| `--port` | int | 8000 | 模型服务端口 |
| `--expected-ttft-gain` | float | None | 预期TTFT性能提升倍数 |
| `--expected-latency-gain` | float | None | 预期延迟性能提升倍数 |

### RAG测试

RAG（检索增强生成）测试用于评估模型在使用外部知识时的性能和质量，特别关注模型基于提供的文档回答问题的能力。

#### 安装额外依赖

```bash
pip install openai pandas rouge_score
```

#### 准备测试数据集

创建一个JSON格式的测试数据集，包含问题、答案和上下文信息：

```json
[
    {
        "question": "What is the capital of France?",
        "answers": ["Paris"],
        "ctxs": [
            {
                "title": "France",
                "text": "France is a country in Western Europe. Its capital is Paris."
            }
        ]
    },
    {
        "question": "What is the largest planet in our solar system?",
        "answers": ["Jupiter"],
        "ctxs": [
            {
                "title": "Solar System",
                "text": "The solar system consists of the Sun and the objects that orbit it. Jupiter is the largest planet in our solar system."
            }
        ]
    }
]
```

#### 运行RAG测试

```bash
# 基本RAG测试（QA模式）
python tests/testrag/rag.py --qps 1  --dataset tests/testrag/test_dataset.json --prompt-build-method QA --base-url "http://192.168.0.126:30180/v1" --model "Qwen/Qwen3-8B" 
```

#### RAG测试参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--qps` | float | 必填 | 整体QPS（每秒查询数） |
| `--model` | str | 必填 | 模型名称 |
| `--tokenizer` | str | "" | 分词器名称（默认使用模型名称） |
| `--dataset` | str | 必填 | 数据集路径 |
| `--start-index` | int | 0 | 工作负载起始索引 |
| `--end-index` | int | -1 | 工作负载结束索引（-1表示到最后） |
| `--shuffle` | bool | False | 是否随机打乱数据集 |
| `--system-prompt` | str | "" | 系统提示词 |
| `--separator` | str | "" | 分隔符 |
| `--query-prompt` | str | "" | 查询提示词 |
| `--prompt-build-method` | str | 必填 | 提示词构建方法（QA/FEW_SHOT） |
| `--base-url` | str | 必填 | 服务端点地址 |
| `--api-key` | str | "EMPTY" | API密钥 |
| `--output` | str | "summary.csv" | 输出文件名 |
| `--warmup` | bool | False | 是否启用预热 |
| `--time` | int | None | 总运行时间（秒） |
| `--verbose` | bool | False | 是否启用详细日志 |
| `--max-tokens` | int | 32 | 每次生成的最大token数 |
| `--step-interval` | float | 0.02 | 步进间隔 |

### 多语种翻译质量评估测试

多语种翻译质量评估测试用于评估模型将多种语言翻译成中文的质量，采用反向翻译评估方法：将各语种文本翻译成中文后，与标准中文翻译进行对比评分。

#### 安装额外依赖

```bash
pip install pandas openpyxl
```

#### 准备测试数据

测试数据需要是一个Excel文件，包含以下工作表：
- **索引表**：包含素材编号、行业、标准中文翻译
- **各语种表**：包含素材编号和各语种的原文

示例数据格式：
- 索引表：`material_id`, `industry`, `content_cn`
- 语种表：`material_id`, `英语`, `日语`, `韩语`, ...

#### 运行多语种翻译质量评估测试

```bash
# 基本测试（使用同一个模型进行翻译和评估）
python tests/mtqs/main-new.py --excel-file data/mtqs/语种语料V2.xlsx --model-a-url "http://192.168.0.126:30180/v1/chat/completions" --model-b-url "http://192.168.0.126:30180/v1/chat/completions"  --concurrency 1 --translate-model "Qwen/Qwen3-8B" --evaluate-model "Qwen/Qwen3-8B"
```

#### 多语种翻译质量评估参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--excel-file` | str | 必填 | 语种语料 Excel 文件路径 |
| `--model-a-url` | str | None | 翻译模型 API URL |
| `--model-b-url` | str | None | 评估模型 API URL（可选，默认使用model-a-url） |
| `--translate-model` | str | None | 用于翻译步骤的模型名 |
| `--evaluate-model` | str | None | 用于评估步骤的模型名 |
| `--concurrency` | int | 1 | 模型请求的并发数 |
| `--output-file` | str | reverse_translation_results.json | 结果输出文件名 |
| `--debug` | bool | False | 调试模式：只检查数据结构，不执行翻译 |

#### 测试结果

测试完成后会生成JSON格式的结果文件，包含：
- 总体平均分
- 各素材的详细评估结果
- 每个语种的翻译质量和得分



## 测试结果示例

```
开始测试: 总请求数=2, 输入token数=200, 输出token数=150, 忽略EOS=False
使用模型: openai
============================================================
开始执行 2 个请求...
[===============---------------] 1/2 (50.0%) - 缓存命中: 是
[==============================] 2/2 (100.0%) - 缓存命中: 否
测试完成，共执行 2 个请求
测试结果:
============================================================
总请求数: 2
输入token数: 200
输出token数: 150
平均TTFT: 0.1500秒
输入token吞吐率: 46.50 tokens/秒
平均单个请求延迟总时间: 2.7954秒
所有请求耗时: 2.7966秒
总请求数: 2
缓存命中率: 50.00%
============================================================
```

## 项目结构

```
model_bench/
├── src/                # 源代码目录
│   ├── __init__.py
│   ├── core.py          # 核心测试功能
│   ├── model_adapter.py # 模型接口适配器
│   ├── main.py          # 命令行界面
│   └── report.py        # 报告生成功能
├── tests/              # 测试目录
│   ├── long_doc_qa.py   # 长文档测试脚本
│   ├── multi_doc_qa.py  # 多文档测试脚本
│   ├── mtqs/            # 多语种翻译质量评估测试目录
│   │   └── main-new.py  # 多语种翻译质量评估测试脚本
│   └── testrag/         # RAG测试目录
│       ├── rag.py       # RAG测试脚本
│       ├── precompute.py # KV缓存预计算脚本
│       └── utils.py     # 工具函数
├── data/               # 数据目录
│   ├── vocab.json       # 词汇表文件
│   ├── translate/       # 翻译数据集
│   └── mtqs/            # 多语种翻译质量评估测试数据集
├── .trae/              # Trae IDE配置
├── venv/               # 虚拟环境
├── requirements.txt    # 依赖配置
├── download_huggingface_dataset.py # 数据集下载脚本
├── test_report.csv     # 测试报告示例
├── test_report.json    # 测试报告示例
├── .gitignore          # Git忽略文件
└── README.md           # 项目说明
```

## 注意事项

1. 使用OpenAI模型时，需要提供有效的API密钥
2. 使用本地模型时，需要提供模型路径
3. 测试结果会受到网络环境、模型负载等因素的影响
4. 对于大规模测试，建议使用`--max-concurrency`参数限制并发数，避免对模型服务造成过大压力

## Docker支持

### 构建Docker镜像

```bash
# 在项目根目录运行
docker build -t model-bench .
```

### 运行Docker容器

```bash
# 基本运行
docker run model-bench --total 1 --input-tokens 100 --output-tokens 100

# 使用自定义参数
docker run model-bench --total 5 --max-concurrency 2 --input-tokens 150 --output-tokens 100 --model-type openai --api-key your_api_key --base-url http://host.docker.internal:30180/v1/chat/completions

# 挂载数据目录（用于自定义数据）
docker run -v ./data:/app/data model-bench --total 1 --input-tokens 100 --output-tokens 100 --input-data-type custom --custom-data-path /app/data/translate/btranslate.json
```

### Docker Compose（可选）

创建`docker-compose.yml`文件：

```yaml
version: '3.8'
services:
  model-bench:
    build: .
    image: model-bench
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
    command: --total 1 --input-tokens 100 --output-tokens 100
```

然后运行：

```bash
docker-compose up
```

## 许可证

[MIT License](LICENSE)