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
├── src/
│   ├── __init__.py
│   ├── core.py          # 核心测试功能
│   ├── model_adapter.py # 模型接口适配器
│   ├── main.py          # 命令行界面
│   └── report.py        # 报告生成功能
├── tests/              # 测试文件
├── venv/               # 虚拟环境
├── requirements.txt    # 依赖配置
└── README.md           # 项目说明
```

## 注意事项

1. 使用OpenAI模型时，需要提供有效的API密钥
2. 使用本地模型时，需要提供模型路径
3. 测试结果会受到网络环境、模型负载等因素的影响
4. 对于大规模测试，建议使用`--max-concurrency`参数限制并发数，避免对模型服务造成过大压力

## 许可证

[MIT License](LICENSE)