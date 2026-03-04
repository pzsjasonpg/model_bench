# config.py
import os

class Config:
    # API配置
    DEFAULT_MODEL_A_URL = os.getenv('MODEL_A_URL', 'http://192.168.0.126:9101/v1/completions')
    DEFAULT_MODEL_B_URL = os.getenv('MODEL_B_URL', 'http://192.168.0.126:9102/v1/completions')
    
    # 千问API配置（阿里云百炼）
    QWEN_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')  # 阿里云API Key
    QWEN_MODEL_NAME = os.getenv('QWEN_MODEL_NAME', 'qwen-plus')  # 默认使用qwen-plus模型
    QWEN_API_URL = os.getenv('QWEN_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
    
    # 评估配置
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    DELAY_BETWEEN_REQUESTS = 1  # 秒
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    
    # 输出配置
    DEFAULT_OUTPUT_FILE = 'translation_evaluation_results.json'
    SAVE_DETAILED_RESULTS = True