import argparse
import sys
from .core import ModelPerfTest
from .model_adapter import get_model_adapter
from .report import ReportGenerator

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="模型性能测试工具")
    
    # 基本测试参数
    parser.add_argument('--total', type=int, default=1, help='总请求的条数')
    parser.add_argument('--max-concurrency', type=int, help='最大并发数')
    parser.add_argument('--input-tokens', type=int, default=100, help='输入token数')
    parser.add_argument('--output-tokens', type=int, default=100, help='输出token数')
    parser.add_argument('--ignore-eos', action='store_true', help='忽略EOS token，不截断输出')
    
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

def main():
    """主函数"""
    args = parse_args()
    
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
        input_tokens=args.input_tokens,
        output_tokens=args.output_tokens,
        model_adapter=model_adapter,
        max_concurrency=args.max_concurrency,
        model_name=args.model,
        ignore_eos=args.ignore_eos
    )
    
    # 运行测试
    print(f"开始测试: 总请求数={args.total}, 最大并发数={args.max_concurrency}, 输入token数={args.input_tokens}, 输出token数={args.output_tokens}, 忽略EOS={args.ignore_eos}")
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