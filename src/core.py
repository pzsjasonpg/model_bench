import time
import threading
import concurrent.futures
from typing import List, Dict, Any, Optional
from .model_adapter import ModelAdapter, get_model_adapter

class ModelPerfTest:
    def __init__(self, total: int, input_tokens: int, output_tokens: int, model_adapter: Optional[ModelAdapter] = None, max_concurrency: Optional[int] = None, model_name: Optional[str] = None):
        self.total = total
        self.max_concurrency = max_concurrency
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model_adapter = model_adapter or get_model_adapter("mock")
        self.model_name = model_name
        self.results = []
    
    def generate_test_prompt(self) -> str:
        """生成指定长度的测试prompt"""
        import random
        import string
        
        # 生成随机文本，确保每个请求的prompt不同
        # 生成足够长度的随机字符串
        # 假设平均每个字符是0.7个token（中文），所以需要生成更多字符
        char_count = int(self.input_tokens * 1.4)  # 适当调整以达到目标token数
        
        # 生成包含中文和英文的随机文本
        chinese_chars = ''.join(chr(random.randint(0x4e00, 0x9fff)) for _ in range(char_count // 2))
        english_chars = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=char_count // 2))
        
        # 混合中文和英文
        combined = list(chinese_chars + english_chars)
        random.shuffle(combined)
        prompt = ''.join(combined)
        
        # 确保prompt长度合适
        prompt = prompt[:char_count]
        
        return prompt
    
    def test_single_request(self) -> Dict[str, Any]:
        """测试单个请求的性能"""
        start_time = time.time()
        
        # 生成测试prompt
        prompt = self.generate_test_prompt()
        
        # 调用模型API
        result = self.model_adapter.generate(prompt, self.output_tokens)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        return {
            "input_tokens": result.get("input_tokens", self.input_tokens),
            "output_tokens": result.get("output_tokens", self.output_tokens),
            "ttft": result.get("ttft", 0),
            "total_time": total_time,
            "start_time": start_time,
            "end_time": end_time,
            "cache_hit": result.get("cache_hit", False)
        }
    
    def run_concurrent_tests(self) -> List[Dict[str, Any]]:
        """运行并发测试"""
        self.results = []
        completed = 0
        total = self.total
        
        print(f"开始执行 {total} 个请求...")
        
        # 使用max_concurrency限制最大并发数
        max_workers = self.max_concurrency if self.max_concurrency is not None else self.total
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_result = {executor.submit(self.test_single_request): i for i in range(self.total)}
            for future in concurrent.futures.as_completed(future_to_result):
                try:
                    result = future.result()
                    self.results.append(result)
                    completed += 1
                    # 打印进度条
                    progress = (completed / total) * 100
                    bar_length = 30
                    filled_length = int(bar_length * completed // total)
                    bar = '=' * filled_length + '-' * (bar_length - filled_length)
                    cache_hit = result.get('cache_hit', False)
                    print(f'[{bar}] {completed}/{total} ({progress:.1f}%) - 缓存命中: {"是" if cache_hit else "否"}')
                except Exception as exc:
                    print(f'测试请求发生异常: {exc}')
                    completed += 1
                    # 打印进度条
                    progress = (completed / total) * 100
                    bar_length = 30
                    filled_length = int(bar_length * completed // total)
                    bar = '=' * filled_length + '-' * (bar_length - filled_length)
                    print(f'[{bar}] {completed}/{total} ({progress:.1f}%) - 异常')
        
        print(f"测试完成，共执行 {completed} 个请求")
        return self.results
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.results:
            return {
                "total": self.total,
                "max_concurrency": self.max_concurrency,
                "model_name": self.model_name,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "avg_ttft": 0,
                "min_ttft": 0,
                "max_ttft": 0,
                "input_throughput": 0,
                "output_throughput": 0,
                "avg_total_time": 0,
                "min_total_time": 0,
                "max_total_time": 0,
                "all_requests_time": 0,
                "total_requests": 0,
                "cache_hit_rate": 0
            }
        
        # 计算TTFT平均值（转换为毫秒）
        avg_ttft = sum(r['ttft'] for r in self.results) / len(self.results) * 1000
        
        # 计算TTFT最小和最大值（转换为毫秒）
        min_ttft = min(r['ttft'] for r in self.results) * 1000
        max_ttft = max(r['ttft'] for r in self.results) * 1000
        
    
        # 计算单个请求延迟总时间
        avg_total_time = sum(r['total_time'] for r in self.results) / len(self.results)
        
        # 计算最小和最大耗时
        min_total_time = min(r['total_time'] for r in self.results)
        max_total_time = max(r['total_time'] for r in self.results)
        
        # 计算所有请求耗时
        all_requests_time = max(r['end_time'] for r in self.results) - min(r['start_time'] for r in self.results)

        # 计算输入token吞吐率 (tokens/second)
        input_throughput = sum(r['input_tokens'] for r in self.results) / all_requests_time
        
        # 计算输出token吞吐率 (tokens/second)
        output_throughput = sum(r['output_tokens'] for r in self.results) / all_requests_time
        
        
        # 计算缓存命中率
        cache_hits = sum(1 for r in self.results if r.get('cache_hit', False))
        cache_hit_rate = cache_hits / len(self.results) if len(self.results) > 0 else 0
        
        return {
            "total": self.total,
            "max_concurrency": self.max_concurrency,
            "model_name": self.model_name,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "avg_ttft": avg_ttft,
            "min_ttft": min_ttft,
            "max_ttft": max_ttft,
            "input_throughput": input_throughput,
            "output_throughput": output_throughput,
            "avg_total_time": avg_total_time,
            "min_total_time": min_total_time,
            "max_total_time": max_total_time,
            "all_requests_time": all_requests_time,
            "total_requests": len(self.results),
            "cache_hit_rate": cache_hit_rate
        }
    
    def run(self) -> Dict[str, Any]:
        """运行完整测试并返回结果"""
        self.run_concurrent_tests()
        return self.calculate_metrics()