import requests
import time
import json
from typing import Dict, Any, Optional

class ModelAdapter:
    """模型接口适配器基类"""
    def generate(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """生成文本"""
        raise NotImplementedError

class OpenAIAdapter(ModelAdapter):
    """OpenAI API适配器"""
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: str = "https://api.openai.com/v1/chat/completions"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
    
    def generate(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": True
        }
        
        # 记录开始时间
        start_time = time.time()
        
        # 发送流式请求
        response = requests.post(self.base_url, headers=headers, json=data, stream=True)
        response.raise_for_status()
        
        # 初始化变量
        text = ""
        input_tokens = 0
        output_tokens = 0
        ttft = None
        
        # 处理流式响应
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                # 解码 chunk
                chunk_str = chunk.decode('utf-8')
                # 分割 SSE 事件
                events = chunk_str.split('\n\n')
                for event in events:
                    if event.startswith('data: '):
                        data_str = event[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            # 检查是否有选择
                            if 'choices' in data and data['choices']:
                                choice = data['choices'][0]
                                # 记录TTFT
                                if ttft is None and 'delta' in choice and choice['delta'] and 'content' in choice['delta']:
                                    ttft = time.time() - start_time
                                # 累加文本
                                if 'delta' in choice and choice['delta'] and 'content' in choice['delta'] and choice['delta']['content'] is not None:
                                    text += choice['delta']['content']
                                # 获取 usage 信息（在最后一个 chunk）
                                if 'usage' in data and data['usage']:
                                    input_tokens = data['usage'].get('prompt_tokens', 0)
                                    output_tokens = data['usage'].get('completion_tokens', 0)
                        except json.JSONDecodeError:
                            pass
        
        # 如果没有获取到 usage 信息，估算 token 数
        if input_tokens == 0:
            input_tokens = len(prompt.split()) * 1.3
        if output_tokens == 0:
            output_tokens = len(text.split()) * 1.3
        
        # 检查响应头中是否有缓存相关信息
        # 这里简化处理，模拟缓存命中率
        # 实际使用时，应该根据响应头或其他方式判断缓存命中
        import random
        cache_hit = random.choice([True, False])
        
        return {
            "text": text,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "ttft": ttft if ttft is not None else 0,
            "cache_hit": cache_hit
        }

class LocalModelAdapter(ModelAdapter):
    """本地模型适配器"""
    def __init__(self, model_path: str, command: str = "python"):
        self.model_path = model_path
        self.command = command
        # 这里可以加载本地模型
        # 例如使用transformers库加载模型
    
    def generate(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        # 模拟本地模型生成
        # 实际使用时，这里会调用真实的本地模型
        import time
        time.sleep(1)  # 模拟模型推理时间
        
        # 简单计算token数
        input_tokens = len(prompt.split()) * 1.3  # 假设平均每个单词1.3个token
        output_tokens = min(max_tokens, 100)  # 模拟输出token数
        
        # 模拟缓存命中率
        import random
        cache_hit = random.choice([True, False])
        
        return {
            "text": f"这是本地模型的生成结果，基于输入: {prompt[:50]}...",
            "input_tokens": int(input_tokens),
            "output_tokens": output_tokens,
            "cache_hit": cache_hit
        }

class MockModelAdapter(ModelAdapter):
    """模拟模型适配器，用于测试"""
    def generate(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        import time
        time.sleep(0.5)  # 模拟模型推理时间
        
        # 改进token数计算
        # 对于中文，假设每个字符是1个token
        # 对于英文，假设每个单词是1.3个token
        chinese_chars = sum(1 for c in prompt if '\u4e00' <= c <= '\u9fff')
        english_parts = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in prompt)
        english_words = len(english_parts.split())
        
        input_tokens = chinese_chars + int(english_words * 1.3)
        # 确保输入token数至少为1
        input_tokens = max(input_tokens, 1)
        
        output_tokens = min(max_tokens, 100)  # 模拟输出token数
        
        # 模拟缓存命中率
        import random
        cache_hit = random.choice([True, False])
        
        return {
            "text": f"这是模拟模型的生成结果，基于输入: {prompt[:50]}...",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": cache_hit
        }

# 模型适配器工厂
def get_model_adapter(model_type: str, **kwargs) -> ModelAdapter:
    """获取模型适配器"""
    if model_type == "openai":
        return OpenAIAdapter(**kwargs)
    elif model_type == "local":
        return LocalModelAdapter(**kwargs)
    elif model_type == "mock":
        return MockModelAdapter()
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")