import argparse
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import ModelPerfTest
from model_adapter import get_model_adapter
from report import ReportGenerator

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="模型性能测试工具")
    
    # 基本测试参数
    parser.add_argument('--total', type=int, default=1, help='总请求的条数')
    parser.add_argument('--max-concurrency', type=int, help='最大并发数')
    parser.add_argument('--input-tokens', type=str, default='100', help='输入token数（可以是范围，如"100-200"）')
    parser.add_argument('--output-tokens', type=str, default='100', help='输出token数（可以是范围，如"100-200"）')
    parser.add_argument('--ignore-eos', action='store_true', help='忽略EOS token，不截断输出')
    parser.add_argument('--rounds', type=int, default=0, help='多轮问答次数，大于0时启用多轮问答')
    parser.add_argument('--wait-rounds', action='store_true', help='多轮对话时，等待当前轮次所有请求完成后再开始下一轮')
    parser.add_argument('--input-data-type', type=str, default='random', choices=['random', 'custom'], help='输入数据类型：random（随机生成数据）或custom（自定义数据）')
    parser.add_argument('--custom-data-path', type=str, help='自定义数据文件路径，当input-data-type为custom时使用')
    parser.add_argument('--scenario', type=str, choices=['summary', 'translate', 'entity_extraction'], help='查询场景参数，设置为summary时启用摘要场景，设置为translate时启用翻译场景，设置为entity_extraction时启用实体抽取场景')
    parser.add_argument('--enable-thinking', action='store_true', help='开启思考模式，默认不开启')
    
    # 模型相关参数
    parser.add_argument('--model-type', type=str, default='mock', choices=['mock', 'openai', 'local'], help='模型类型')
    parser.add_argument('--api-key', type=str, help='OpenAI API密钥')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='模型名称')
    parser.add_argument('--model-path', type=str, help='本地模型路径')
    parser.add_argument('--base-url', type=str, help='模型请求地址')
    parser.add_argument('--command', type=str, default='python', help='本地模型命令名')
    
    # 报告相关参数
    parser.add_argument('--report-format', type=str, default='text', choices=['text', 'json', 'csv'], help='报告格式')
    parser.add_argument('--output-file', type=str, help='报告输出文件路径')
    
    return parser.parse_args()

def parse_token_range(token_str):
    """解析token数范围"""
    if '-' in token_str:
        min_val, max_val = token_str.split('-')
        return int(min_val), int(max_val)
    else:
        val = int(token_str)
        return val, val

def main():
    """主函数"""
    args = parse_args()
    
    # 解析token数范围
    input_tokens_min, input_tokens_max = parse_token_range(args.input_tokens)
    output_tokens_min, output_tokens_max = parse_token_range(args.output_tokens)
    
    # 获取模型适配器
    model_kwargs = {}
    if args.model_type == 'openai':
        if not args.api_key:
            print("错误: 使用OpenAI模型时需要提供API密钥")
            sys.exit(1)
        model_kwargs['api_key'] = args.api_key
        model_kwargs['model'] = args.model
        if args.base_url:
            model_kwargs['base_url'] = args.base_url
    elif args.model_type == 'local':
        if not args.model_path:
            print("错误: 使用本地模型时需要提供模型路径")
            sys.exit(1)
        model_kwargs['model_path'] = args.model_path
        model_kwargs['command'] = args.command
    
    model_adapter = get_model_adapter(args.model_type, **model_kwargs)
    
    # 创建测试实例
    test = ModelPerfTest(
        total=args.total,
        input_tokens=(input_tokens_min, input_tokens_max),
        output_tokens=(output_tokens_min, output_tokens_max),
        model_adapter=model_adapter,
        max_concurrency=args.max_concurrency,
        model_name=args.model,
        ignore_eos=args.ignore_eos,
        rounds=args.rounds,
        wait_rounds=args.wait_rounds,
        input_data_type=args.input_data_type,
        custom_data_path=args.custom_data_path,
        scenario=args.scenario,
        enable_thinking=args.enable_thinking
    )

    # 运行测试
    print(f"开始测试: 总请求数={args.total}, 最大并发数={args.max_concurrency}, 输入token数={args.input_tokens}, 输出token数={args.output_tokens}, 忽略EOS={args.ignore_eos}, 多轮问答次数={args.rounds}, 轮次等待={args.wait_rounds}")
    print(f"输入数据类型: {args.input_data_type}, 自定义数据路径: {args.custom_data_path}")
    print(f"查询场景: {args.scenario}, 思考模式: {args.enable_thinking}")
    print(f"使用模型: {args.model_type}, 模型名: {args.model}")
    print("=" * 60)
    
    metrics = test.run()
    
    # 显示测试结果
    print("测试结果:")
    print("=" * 60)
    print(f"总请求数: {metrics['total']}")
    print(f"最大并发数: {metrics['max_concurrency']}")
    print(f"模型名: {metrics['model_name']}")
    print(f"输入token数: {metrics['input_tokens']}")
    print(f"输出token数: {metrics['output_tokens']}")
    print(f"平均TTFT: {metrics['avg_ttft']:.4f}毫秒")
    print(f"最小TTFT: {metrics['min_ttft']:.4f}毫秒")
    print(f"最大TTFT: {metrics['max_ttft']:.4f}毫秒")
    print(f"输入token吞吐率: {metrics['input_throughput']:.2f} tokens/秒")
    print(f"输出token吞吐率: {metrics['output_throughput']:.2f} tokens/秒")
    print(f"平均单个请求延迟总时间: {metrics['avg_total_time']:.4f}秒")
    print(f"最小单个请求延迟总时间: {metrics['min_total_time']:.4f}秒")
    print(f"最大单个请求延迟总时间: {metrics['max_total_time']:.4f}秒")
    print(f"所有请求耗时: {metrics['all_requests_time']:.4f}秒")
    print(f"总请求数: {metrics['total_requests']}")
    print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
    print(f"所有请求输入token总数: {metrics['total_input_tokens']:.0f}")
    print(f"所有请求输出token总数: {metrics['total_output_tokens']:.0f}")
    print("=" * 60)
    
    # 生成报告
    if args.report_format or args.output_file:
        report_generator = ReportGenerator()
        report_result = report_generator.generate_report(
            metrics,
            format=args.report_format,
            output_file=args.output_file
        )
        print(report_result)

if __name__ == "__main__":
    main()