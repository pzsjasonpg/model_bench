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

### 基本用法

```bash
python -m src.main --total 2 --input-tokens 200 --output-tokens 150
```

### 测试指定模型

```bash
# 测试OpenAI模型
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type openai --api-key your_api_key

# 测试本地模型
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type local --model-path ./model

# 测试指定模型地址
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --model-type openai --api-key test_key --base-url http://localhost:8000/v1/chat/completions --model gpt-3.5-turbo
```

### 使用最大并发数限制

```bash
# 总请求数为5，但最大并发数为2（分批执行）
python -m src.main --total 5 --max-concurrency 2 --input-tokens 100 --output-tokens 50
```

### 使用忽略EOS参数

```bash
# 测试时忽略EOS token，不截断输出
python -m src.main --total 10 --max-concurrency 3 --input-tokens 150 --output-tokens 100 --ignore-eos
```

### 多轮问答测试

```bash
# 启用多轮问答，设置5轮
python -m src.main --total 2 --max-concurrency 1 --input-tokens 100 --output-tokens 100 --rounds 5

# 启用多轮问答，设置3轮，等待轮次模式
python -m src.main --total 3 --max-concurrency 2 --input-tokens 100 --output-tokens 100 --rounds 3 --wait-rounds
```

### 使用自定义数据

```bash
# 使用自定义数据文件
python -m src.main --total 5 --max-concurrency 2 --input-tokens 100 --output-tokens 100 --input-data-type custom --custom-data-path path/to/data.json
```

### 使用查询场景

```bash
# 使用摘要场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 150 --output-tokens 100 --scenario summary

# 使用翻译场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 150 --output-tokens 100 --scenario translate

# 使用实体抽取场景
python -m src.main --total 1 --max-concurrency 1 --input-tokens 150 --output-tokens 100 --scenario entity_extraction
```

### 控制思考模式

```bash
# 启用思考模式
python -m src.main --total 1 --max-concurrency 1 --input-tokens 100 --output-tokens 100 --enable-thinking
```

### 生成测试报告

```bash
# 生成JSON格式报告
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --report-format json --output-file report.json

# 生成CSV格式报告
python -m src.main --total 2 --input-tokens 200 --output-tokens 150 --report-format csv --output-file report.csv
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--total` | int | 1 | 总请求的条数 |
| `--max-concurrency` | int | None | 最大并发数（限制实际并发执行的请求数） |
| `--input-tokens` | int | 100 | 输入token数 |
| `--output-tokens` | int | 100 | 输出token数 |
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
├── data/               # 数据目录
│   ├── vocab.json       # 词汇表文件
│   └── translate/       # 翻译数据集
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

## 许可证

[MIT License](LICENSE)