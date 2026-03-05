"""
反向翻译质量评估系统 - 专用版本
翻译方向：其他语种 → 中文

功能说明:
1. 从 Excel 读取各语种的源语言文本
2. 使用大模型 A 将源语言文本翻译成中文
3. 使用大模型 B 评估翻译质量（与标准中文翻译对比）
4. 输出详细的评估报告和 JSON 结果

使用方法:
python main-new.py --excel-file 语种语料V2.xlsx --model-a-url http://xxx --model-b-url http://yyy
"""

import pandas as pd
import requests
import json
import time
import re
from tqdm import tqdm
import argparse
from typing import Dict, List, Tuple
import logging
import sys
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志 - 添加更清晰的格式
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)


class ReverseTranslationEvaluator:
    """
    反向翻译评估器（其他语种 → 中文）
    
    核心流程:
    1. 读取各语种源文本和标准中文翻译
    2. 调用大模型 A 进行翻译（源语言→中文）
    3. 调用大模型 B 进行质量评估
    4. 生成评估报告
    """
    
    def __init__(self, model_a_url: str, model_b_url: str, excel_file: str, concurrency: int = 1, translate_model: str = None, evaluate_model: str = None):
        """
        初始化评估器
        
        Args:
            model_a_url: 大模型 A API URL（用于翻译：源语言→中文）
            model_b_url: 大模型 B API URL（用于评分）
            excel_file: Excel 文件路径
            concurrency: 模型请求的并发数
            translate_model: 用于翻译步骤的模型名
            evaluate_model: 用于评估步骤的模型名
        """
        self.model_a_url = self._normalize_url(model_a_url)
        self.model_b_url = self._normalize_url(model_b_url) if model_b_url else None
        self.excel_file = excel_file
        self.concurrency = concurrency
        self.translate_model = translate_model
        self.evaluate_model = evaluate_model
        self.results = {}
        
        # 固定目标语言为中文
        self.target_language = '中文'
    
    def _normalize_url(self, url: str) -> str:
        """
        规范化API URL，自动补全端点路径
        
        Args:
            url: 原始URL
            
        Returns:
            规范化后的URL
        """
        if not url:
            return url
        
        # 如果URL已经包含完整的端点路径，直接返回
        if '/completions' in url or '/chat/completions' in url:
            return url
        
        # 如果URL以/v1结尾，添加chat/completions端点
        if url.endswith('/v1'):
            return url + '/chat/completions'
        
        # 如果URL以/结尾，添加v1/chat/completions端点
        if url.endswith('/'):
            return url + 'v1/chat/completions'
        
        # 其他情况，添加/v1/chat/completions端点
        return url + '/v1/chat/completions'
        
    def read_excel_data(self) -> Dict:
        """
        读取 Excel 文件中的数据
        
        数据结构:
        - 索引表：包含素材编号、行业、标准中文翻译 (content_cn)
        - 语种 sheet(1-10)：包含各语种的源语言文本 (content)
        
        Returns:
            {
                'index': {素材编号：{industry, standard_chinese}},
                'source_texts': {语种：{素材编号：source_text}}
            }
        """
        try:
            logger.info("开始读取 Excel 数据...")
            
            # 读取索引表
            index_df = pd.read_excel(self.excel_file, sheet_name='索引')
            
            data = {
                'index': {},
                'source_texts': {}
            }
            
            # 处理索引数据 - 提取标准中文翻译
            for idx, row in index_df.iterrows():
                if idx >= 10:  # 只处理前 10 条
                    break
                    
                # 跳过表头行
                if idx == 0 and str(row['编号']).lower() in ['编号', 'id', 'number']:
                    continue
                
                material_id = int(row['编号'])
                industry = row['行业']
                standard_chinese = row['content_cn']
                
                data['index'][material_id] = {
                    'industry': industry,
                    'standard_chinese': standard_chinese
                }
            
            # 读取各语种 sheet - 提取源语言文本
            for i in range(1, 11):  # sheet 1-10
                sheet_name = str(i)
                try:
                    df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
                    
                    logger.info(f"开始处理语种 sheet '{sheet_name}'，共 {len(df)} 行")
                    
                    material_idx = i
                    # 遍历每种语言的翻译
                    for idx, row in df.iterrows():
                        # 跳过表头
                        if pd.isna(row['language']) or pd.isna(row['content']):
                            continue
                        
                        source_language = row['language']  # 源语言
                        source_text = row['content']       # 源语言文本
                        
                        # 使用素材编号作为外层键（从索引表的行顺序获取）
                        # 正确的数据结构：data['source_texts'][material_idx][source_language]
                        if material_idx not in data['source_texts']:
                            data['source_texts'][material_idx] = {}
                        
                        data['source_texts'][material_idx][source_language] = source_text
                        logger.debug(f"  素材 {material_idx} - 语种 '{source_language}': {source_text[:30]}...")
                    
                    logger.info(f"成功读取素材 sheet '{sheet_name}' 的数据")
                    
                except Exception as e:
                    logger.warning(f"读取素材 sheet {sheet_name} 时出错：{e}")
            
            logger.info(f"✓ 读取 {len(data['index'])} 条素材")
            logger.info(f"✓ 读取 {len(data['source_texts'])} 个语种")
            logger.info(f"翻译方向：各语种 → 中文")
            
            return data
            
        except Exception as e:
            logger.error(f"✗ 读取 Excel 失败：{e}")
            raise
    
    def translate_to_chinese(self, source_text: str, source_language: str) -> str:
        """
        使用大模型 A 或千问 API 将源语言文本翻译成中文
        
        Args:
            source_text: 源语言文本（待翻译）
            source_language: 源语言名称
            
        Returns:
            翻译后的中文文本
        """
        try:
            # 判断使用哪种翻译方式
            if self.model_a_url:
                # 使用自定义大模型 A 进行翻译
                logger.debug(f"使用大模型 A 翻译：{source_language}")
                return self._translate_with_model_a(source_text, source_language)
            else:
                # 使用千问 API 进行翻译
                logger.debug(f"使用千问 API 翻译：{source_language}")
                return self._translate_with_qwen_api(source_text, source_language)
                
        except Exception as e:
            logger.error(f"✗ 翻译异常：{e}")
            return ""
    
    def _translate_with_model_a(self, source_text: str, source_language: str) -> str:
        """
        使用大模型 A 将源语言文本翻译成中文
        
        Args:
            source_text: 源语言文本
            source_language: 源语言名称
            
        Returns:
            翻译后的中文文本
        """
        try:
            # 构建提示词：明确要求翻译成中文
            prompt = (
                f"作为专业的翻译专家，请将以下{source_language}原文翻译成中文。\n"
                f"要求：\n"
                f"1. 除了返回翻译结果外，不要添加或返回任何额外内容\n"
                f"2. 保持译文简洁准确\n"
                f"\n"
                f"{source_language}原文：{source_text}\n"
                f"中文翻译："
            )
            
            # 计算合适的 token 数
            max_tokens = self._calculate_tokens_for_chinese(source_text)
            
            # 检查是否是 chat completions 端点
            if "/chat/completions" in self.model_a_url:
                # 使用 chat completions 格式
                payload = {
                    "model": self.translate_model or "/models/Qwen3-8B-FP8",  # 模型名称，根据实际情况调整
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    },
                    "temperature": 0.0  # 降低随机性
                }
            else:
                # 使用 completions 格式
                payload = {
                    "model": self.translate_model or "/models/Qwen3-8B-FP8",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.0  # 降低随机性
                }
            
            response = requests.post(
                self.model_a_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查是否是 chat completions 响应格式
                if "/chat/completions" in self.model_a_url:
                    # 解析 chat completions 格式
                    raw_response = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                else:
                    # 解析 completions 格式
                    raw_response = result.get('choices', [{}])[0].get('text', '').strip()
                
                # 清理响应，提取纯净中文
                chinese_translation = self._clean_chinese_translation(raw_response)
                
                # 如果清理后内容过少，尝试备用方法
                if len(chinese_translation) < 10:
                    logger.debug(f"翻译内容过少，使用备用方法")
                    chinese_translation = self._fallback_translate_to_chinese(
                        source_text, source_language
                    )
                
                return chinese_translation
            else:
                logger.error(f"✗ 模型 A 翻译请求失败：{response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"✗ 模型 A 翻译异常：{e}")
            return ""
    
    def _translate_with_qwen_api(self, source_text: str, source_language: str) -> str:
        """
        使用千问 API 将源语言文本翻译成中文
        
        Args:
            source_text: 源语言文本
            source_language: 源语言名称
            
        Returns:
            翻译后的中文文本
        """
        try:
            if not Config.QWEN_API_KEY:
                logger.warning("未配置千问 API Key，无法使用千问 API 翻译")
                return ""
            
            # 构建翻译提示词
            prompt = (
                f"作为专业的翻译专家，请将以下{source_language}原文翻译成中文。\n"
                f"要求：\n"
                f"1. 只返回翻译结果，不要添加任何额外内容\n"
                f"2. 保持译文简洁准确\n"
                f"\n"
                f"{source_language}原文：{source_text}\n"
                f"中文翻译："
            )
            
            payload = {
                "model": Config.QWEN_MODEL_NAME,
                "input": {"prompt": prompt},
                "parameters": {
                    "max_tokens": self._calculate_tokens_for_chinese(source_text),
                    "temperature": 0.0
                }
            }
            
            headers = {
                "Authorization": f"Bearer {Config.QWEN_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                Config.QWEN_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('output', {}).get('text', '').strip()
                
                if raw_response:
                    # 清理响应，提取纯净中文
                    chinese_translation = self._clean_chinese_translation(raw_response)
                    
                    # 如果清理后内容过少，直接使用原始响应
                    if len(chinese_translation) < 10 and raw_response.strip():
                        chinese_translation = raw_response.strip()
                    
                    return chinese_translation
            
            logger.error(f"✗ 千问 API 翻译请求失败：{response.status_code}")
            return ""
            
        except Exception as e:
            logger.error(f"✗ 千问 API 翻译异常：{e}")
            return ""

    def _calculate_tokens_for_chinese(self, source_text: str) -> int:
        """
        计算翻译为中文所需的 token 数
        
        Args:
            source_text: 源语言文本
            
        Returns:
            建议的 token 数量
        """
        char_count = len(source_text)
        
        # 基于源文本长度估算
        if char_count < 50:
            return 100
        elif char_count < 100:
            return 150
        elif char_count < 200:
            return 200
        else:
            return 250
    
    def _fallback_translate_to_chinese(self, source_text: str, source_language: str) -> str:
        """
        备用翻译方法（主方法失败时使用）
        
        Args:
            source_text: 源语言文本
            source_language: 源语言
            
        Returns:
            翻译后的中文
        """
        try:
            simple_prompt = (
                f"将以下{source_language}翻译成中文，只返回译文：\n"
                f"{source_text}"
            )
            
            # 检查是否是 chat completions 端点
            if "/chat/completions" in self.model_a_url:
                # 使用 chat completions 格式
                payload = {
                    "model": self.translate_model or "/models/Qwen3-8B-FP8",  # 模型名称，根据实际情况调整
                    "messages": [
                        {
                            "role": "user",
                            "content": simple_prompt
                        }
                    ],
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    },
                    "max_tokens": 150,
                    "temperature": 0.0
                }
            else:
                # 使用 completions 格式
                payload = {
                    "prompt": simple_prompt,
                    "max_tokens": 150,
                    "temperature": 0.0,
                    "stop": ["\n\n", "用户"]
                }
            
            response = requests.post(
                self.model_a_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查是否是 chat completions 响应格式
                if "/chat/completions" in self.model_a_url:
                    # 解析 chat completions 格式
                    raw_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                else:
                    # 解析 completions 格式
                    raw_text = result.get('choices', [{}])[0].get('text', '').strip()
                
                return self._extract_chinese_content(raw_text)
            
        except Exception as e:
            logger.warning(f"备用翻译也失败：{e}")
        
        return ""
    
    def _clean_chinese_translation(self, raw_text: str) -> str:
        """
        清理翻译响应，提取纯净中文内容
        
        Args:
            raw_text: 原始响应文本
            
        Returns:
            纯净的中文翻译
        """
        if not raw_text:
            return ""
        
        # 移除常见的前缀和标记
        prefixes_to_remove = [
            "翻译：", "译文：", "中文：", "结果：",
            "Translation:", "Result:", "Chinese:",
            "用户：", "User:", "Assistant:", "System:"
        ]
        
        cleaned_text = raw_text.strip()
        for prefix in prefixes_to_remove:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()
                break
        
        # 按行分割，提取包含中文的行
        lines = cleaned_text.split('\n')
        chinese_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过元内容（推理过程等）
            meta_keywords = [
                '思考', '分析', '理解', '处理', '让我', '我需要',
                '好的', '我将', '按照', '要求', '进行'
            ]
            
            if any(keyword in line for keyword in meta_keywords):
                continue
            
            # 检查是否包含中文字符
            if self._contains_chinese(line):
                chinese_lines.append(line)
        
        # 返回最长的中文行
        if chinese_lines:
            return max(chinese_lines, key=len)
        
        # 如果没有找到中文，返回清理后的文本
        return cleaned_text
    
    def _extract_chinese_content(self, raw_text: str) -> str:
        """
        从混合文本中提取中文内容
        
        Args:
            raw_text: 原始文本
            
        Returns:
            提取的中文内容
        """
        if not raw_text:
            return ""
        
        # 查找第一个中文字符的位置
        for i, char in enumerate(raw_text):
            if '\u4e00' <= char <= '\u9fff':
                # 从中文字符开始提取
                return raw_text[i:].split('\n')[0].strip()
        
        return raw_text.strip()
    
    def _contains_chinese(self, text: str) -> bool:
        """
        检查文本是否包含中文字符
        
        Args:
            text: 待检查的文本
            
        Returns:
            是否包含中文
        """
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def evaluate_chinese_quality(
        self, 
        source_text: str,
        translated_chinese: str,
        standard_chinese: str,
        source_language: str
    ) -> float:
        """
        评估中文翻译质量
        
        Args:
            source_text: 源语言文本
            translated_chinese: 模型翻译的中文
            standard_chinese: 标准中文参考
            source_language: 源语言
            
        Returns:
            质量评分 (0-100)
        """
        try:
            # 前置质量检查
            pre_score = self._pre_check_chinese_quality(
                translated_chinese, standard_chinese
            )
            
            # 如果前置检查分数过低，直接返回
            if pre_score < 30:
                logger.warning(f"前置检查失败，分数：{pre_score}")
                return pre_score
            
            # 选择评分方式
            if self.model_b_url:
                return self._score_with_model_b(
                    source_text, translated_chinese, standard_chinese, 
                    source_language, pre_score
                )
            else:
                return self._score_with_qwen_api(
                    source_text, translated_chinese, standard_chinese,
                    source_language, pre_score
                )
                
        except Exception as e:
            logger.error(f"评分异常：{e}")
            return self._pre_check_chinese_quality(translated_chinese, standard_chinese)
    
    def _pre_check_chinese_quality(
        self, 
        translated_chinese: str, 
        standard_chinese: str
    ) -> float:
        """
        前置中文质量检查
        
        Args:
            translated_chinese: 翻译的中文
            standard_chinese: 标准中文
            
        Returns:
            预评分 (0-100)
        """
        if not translated_chinese:
            return 0
        
        score = 100
        
        # 1. 语言一致性检查（必须是中文）
        if not self._contains_chinese(translated_chinese):
            score -= 50
        
        # 2. 中文比例检查
        chinese_ratio = self._calculate_chinese_ratio(translated_chinese)
        if chinese_ratio < 0.5:
            score -= 30
        
        # 3. 长度合理性
        length_ratio = len(translated_chinese) / len(standard_chinese) if standard_chinese else 1
        if length_ratio < 0.3 or length_ratio > 3.0:
            score -= 20
        
        # 4. 重复内容检查
        repetition_penalty = self._check_repetition(translated_chinese)
        score -= repetition_penalty
        
        # 5. 基本质量
        if len(translated_chinese.strip()) < 5:
            score -= 10
        
        return max(score, 0)
    
    def _calculate_chinese_ratio(self, text: str) -> float:
        """
        计算中文字符比例
        
        Args:
            text: 文本
            
        Returns:
            中文字符比例 (0-1)
        """
        if not text:
            return 0
        
        total_chars = len(text)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        
        return chinese_chars / total_chars if total_chars > 0 else 0
    
    def _check_repetition(self, text: str) -> float:
        """
        检查重复内容并返回惩罚分数
        
        Args:
            text: 文本
            
        Returns:
            惩罚分数 (0-30)
        """
        if not text:
            return 0
        
        # 简单分词
        words = text.split()
        if len(words) < 3:
            return 0
        
        from collections import Counter
        word_counts = Counter(words)
        
        # 计算重复率
        total_words = len(words)
        repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)
        repetition_rate = repeated_words / total_words if total_words > 0 else 0
        
        # 惩罚：重复率越高，扣分越多
        return min(repetition_rate * 30, 30)
    
    def _score_with_model_b(
        self,
        source_text: str,
        translated_chinese: str,
        standard_chinese: str,
        source_language: str,
        pre_score: float
    ) -> float:
        """
        使用大模型 B 进行评分
        
        Args:
            source_text: 源语言文本
            translated_chinese: 翻译的中文
            standard_chinese: 标准中文
            source_language: 源语言
            pre_score: 前置检查分数
            
        Returns:
            最终评分
        """
        try:
            prompt = f"""
你是一名专业、严谨、中立的翻译质量评估专家。
你的任务是：对比待评翻译与标准参考翻译，从准确性、完整性、流畅性、专业度四个维度综合打分。
[评估规则]
准确性：是否忠实原文，无增译、漏译、错译、歪曲原意。
完整性：关键信息、逻辑、细节是否完整保留。
流畅性：中文表达是否自然、通顺、符合中文表达习惯。
专业度：术语准确、语句正式得体、无口语化 / 语病。
[输出要求]
只输出0–100 的整数分数，分数越低质量越差，100 分为完美翻译。
请直接给出总分（0-100），不要解释,不闲聊、不修改原文。

【待评估内容】
待评翻译: {translated_chinese}
标准参考: {standard_chinese}
"""
            
            # 检查是否是 chat completions 端点
            if "/chat/completions" in self.model_b_url:
                # 使用 chat completions 格式
                payload = {
                    "model": self.evaluate_model or "/models/Qwen3-8B-FP8",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "chat_template_kwargs": {
                        "enable_thinking": False
                    },
                    "max_tokens": 10,
                    "temperature": 0.0
                }
            else:
                # 使用 completions 格式
                payload = {
                    "model": self.evaluate_model or "/models/Qwen3-8B-FP8",
                    "prompt": prompt,
                    "max_tokens": 10,
                    "temperature": 0.0
                }
            
            # print(payload)
            response = requests.post(
                self.model_b_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            # print("---",payload)
            
            if response.status_code == 200:
                result = response.json()
                # 检查是否是 chat completions 响应格式
                if "/chat/completions" in self.model_b_url:
                    # 解析 chat completions 格式
                    print("---",result)
                    score_text = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    print("----",score_text)
                else:
                    # 解析 completions 格式
                    score_text = result.get('choices', [{}])[0].get('text', '').strip()
                model_score = self._parse_score(score_text)
                
                # 结合前置分数取平均
                final_score = (model_score + pre_score) / 2
                logger.debug(f"模型 B 评分：{model_score}, 最终：{final_score:.1f}")
                
                return final_score
            
            return pre_score
            
        except Exception as e:
            logger.error(f"模型 B 评分异常：{e}")
            return pre_score
    
    def _score_with_qwen_api(
        self,
        source_text: str,
        translated_chinese: str,
        standard_chinese: str,
        source_language: str,
        pre_score: float
    ) -> float:
        """
        使用千问 API 评分
        
        Args:
            source_text: 源语言文本
            translated_chinese: 翻译的中文
            standard_chinese: 标准中文
            source_language: 源语言
            pre_score: 前置检查分数
            
        Returns:
            最终评分
        """
        try:
            if not Config.QWEN_API_KEY:
                logger.warning("未配置千问 API Key")
                return pre_score
            
            prompt = f"""
            你是一名专业、严谨、中立的翻译质量评估专家。
你的任务是：对比待评翻译与标准参考翻译，从准确性、完整性、流畅性、专业度四个维度综合打分。
[评估规则]
准确性：是否忠实原文，无增译、漏译、错译、歪曲原意。
完整性：关键信息、逻辑、细节是否完整保留。
流畅性：中文表达是否自然、通顺、符合中文表达习惯。
专业度：术语准确、语句正式得体、无口语化 / 语病。
[输出要求]
只输出0–100 的整数分数，分数越低质量越差，100 分为完美翻译。
请直接给出总分（0-100），不要解释,不闲聊、不修改原文。

【待评估内容】
待评翻译: {translated_chinese}
标准参考: {standard_chinese}
            """
            
            payload = {
                "model": Config.QWEN_MODEL_NAME,
                "input": {"prompt": prompt},
                "parameters": {
                    "max_tokens": 10,
                    "temperature": 0.0
                }
            }
            
            headers = {
                "Authorization": f"Bearer {Config.QWEN_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                Config.QWEN_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                score_text = result.get('output', {}).get('text', '').strip()
                model_score = self._parse_score(score_text)
                
                final_score = (model_score + pre_score) / 2
                logger.debug(f"千问评分：{model_score}, 最终：{final_score:.1f}")
                
                return final_score
            
            return pre_score
            
        except Exception as e:
            logger.error(f"千问 API 评分异常：{e}")
            return pre_score
    
    def _parse_score(self, score_text: str) -> float:
        """
        解析评分文本
        
        Args:
            score_text: 包含分数的文本
            
        Returns:
            解析出的分数 (0-100)
        """
        if not score_text:
            return 50.0
        
        # 尝试直接转换
        try:
            score = float(score_text.strip())
            if 0 <= score <= 100:
                return score
        except ValueError:
            pass
        
        # 提取数字
        import re
        numbers = re.findall(r'\d+\.?\d*', score_text)
        if numbers:
            for num_str in numbers:
                try:
                    num = float(num_str)
                    if 0 <= num <= 100:
                        return num
                except ValueError:
                    continue
        
        return 50.0  # 默认分数
    
    def _process_language(
        self, 
        source_language: str, 
        source_text: str, 
        standard_chinese: str
    ) -> Dict:
        """
        处理单个语种的翻译和评估
        
        Args:
            source_language: 源语言
            source_text: 源语言文本
            standard_chinese: 标准中文翻译
            
        Returns:
            评估结果字典
        """
        try:
            # 翻译
            translated_chinese = self.translate_to_chinese(str(source_text).strip(), source_language)
            
            if not translated_chinese:
                logger.warning(f"翻译失败：{source_language}")
                return None
            
            # 评分
            score = self.evaluate_chinese_quality(
                str(source_text).strip(),
                translated_chinese,
                standard_chinese,
                source_language
            )
            
            # 记录结果
            evaluation = {
                'source_language': source_language,
                'source_text': str(source_text).strip(),
                'translated_chinese': translated_chinese,
                'standard_chinese': standard_chinese,
                'score': score
            }
            
            return evaluation
        except Exception as e:
            logger.error(f"处理语种 {source_language} 时出错：{e}")
            return None
    
    def process_material(
        self, 
        material_id: int, 
        material_data: Dict,
        source_texts_by_material: Dict
    ) -> Dict:
        """
        处理单条素材的所有语种翻译评估
        
        Args:
            material_id: 素材编号
            material_data: 素材数据（包含 standard_chinese）
            source_texts_by_material: 按素材组织的源文本 {material_id: {language: text}}
            
        Returns:
            评估结果
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"处理素材 {material_id}")
        logger.info(f"{'='*60}")
        
        results = {
            'material_id': material_id,
            'industry': material_data.get('industry', ''),
            'standard_chinese': material_data.get('standard_chinese', ''),
            'evaluations': [],
            'total_score': 0,
            'average_score': 0
        }
        
        standard_chinese = material_data.get('standard_chinese', '')
        
        # 获取该素材的所有语种文本
        if material_id not in source_texts_by_material:
            logger.warning(f"素材 {material_id} 没有语种数据")
            return results
        
        languages_dict = source_texts_by_material[material_id]
        
        # 遍历所有语种
        languages = list(languages_dict.keys())
        total_languages = len(languages)
        
        if total_languages == 0:
            logger.warning(f"素材 {material_id} 没有任何语种数据")
            return results
        
        logger.info(f"开始评估 {total_languages} 个语种 → 中文")
        
        # 准备任务列表
        tasks = []
        for source_language in languages:
            source_text = languages_dict[source_language]
            if not source_text or not str(source_text).strip():
                logger.warning(f"语种 '{source_language}' 的文本为空")
                continue
            tasks.append((source_language, source_text, standard_chinese))
        
        # 使用一个线程池并发处理翻译和评估
        evaluations = []
        if tasks:
            concurrency = min(self.concurrency, len(tasks))
            logger.info(f"使用 {concurrency} 个并发线程处理翻译和评估")
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_to_task = {}
                for task in tasks:
                    source_language, source_text, standard_chinese = task
                    future = executor.submit(
                        self._process_language,
                        source_language,
                        source_text,
                        standard_chinese
                    )
                    future_to_task[future] = source_language
                
                # 处理完成的任务
                for future in as_completed(future_to_task):
                    source_language = future_to_task[future]
                    try:
                        result = future.result()
                        if result:
                            evaluations.append(result)
                            logger.info(f"完成处理：{source_language} → 中文")
                            logger.info(f"原文：{result['source_text']}")
                            logger.info(f"译文：{result['translated_chinese']}")
                            logger.info(f"得分：{result['score']:.2f}/100")
                    except Exception as e:
                        logger.error(f"处理 {source_language} 时出错：{e}")
        
        # 更新结果
        for evaluation in evaluations:
            results['evaluations'].append(evaluation)
            results['total_score'] += evaluation['score']
        
        # 计算平均分
        if results['evaluations']:
            results['average_score'] = results['total_score'] / len(results['evaluations'])
        
        logger.info(f"素材 {material_id} 完成，平均分：{results['average_score']:.2f}")
        
        return results
    
    def run_evaluation(self) -> Dict:
        """
        运行完整的评估流程
        
        Returns:
            总体评估结果
        """
        logger.info("\n" + "="*80)
        logger.info("开始反向翻译评估（各语种 → 中文）")
        logger.info("="*80)
        
        # 读取数据
        data = self.read_excel_data()
        
        overall_results = {
            'materials': [],
            'overall_total_score': 0,
            'overall_average_score': 0,
            'total_evaluations': 0,
            'target_language': self.target_language
        }
        
        # 处理每条素材
        for material_id, material_data in data['index'].items():
            material_result = self.process_material(
                material_id,
                material_data,
                data['source_texts']
            )
            
            overall_results['materials'].append(material_result)
            overall_results['overall_total_score'] += material_result['total_score']
            overall_results['total_evaluations'] += len(material_result['evaluations'])
        
        # 计算总体平均分
        if overall_results['total_evaluations'] > 0:
            overall_results['overall_average_score'] = (
                overall_results['overall_total_score'] / 
                overall_results['total_evaluations']
            )
        
        self.results = overall_results
        
        logger.info("\n" + "="*80)
        logger.info("✓ 评估完成!")
        logger.info(f"总体平均分：{overall_results['overall_average_score']:.2f}/100")
        logger.info("="*80)
        
        return overall_results
    
    def save_results(self, output_file: str = "reverse_translation_results.json"):
        """
        保存评估结果到 JSON 文件
        
        Args:
            output_file: 输出文件名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ 结果已保存到：{output_file}")
            
        except Exception as e:
            logger.error(f"✗ 保存失败：{e}")
    
    def print_summary(self):
        """打印评估摘要"""
        if not self.results:
            logger.warning("没有评估结果")
            return
        
        print("\n" + "="*80)
        print("反向翻译评估结果摘要")
        print("="*80)
        
        print(f"\n总体平均分：{self.results['overall_average_score']:.2f}/100")
        print(f"总评分数：{self.results['overall_total_score']:.2f}")
        print(f"总评估次数：{self.results['total_evaluations']}")
        
        print("\n各素材详情:")
        print("-" * 80)
        
        for material in self.results['materials']:
            print(f"\n素材 {material['material_id']} ({material['industry']}):")
            print(f"  标准中文：{material['standard_chinese'][:50]}...")
            print(f"  平均分：{material['average_score']:.2f}/100")
            print(f"  评估语种数：{len(material['evaluations'])}")
            
            # 显示部分语种的评估
            for eval_item in material['evaluations'][:3]:
                print(f"    - {eval_item['source_language']}: {eval_item['score']:.2f}分")
        
        print("\n" + "="*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='反向翻译质量评估系统（各语种 → 中文）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main-new.py --excel-file 语种语料 V2.xlsx --model-a-url http://192.168.0.126:9101/v1/completions
  python main-new.py --excel-file 语种语料 V2.xlsx --model-a-url http://xxx --model-b-url http://yyy --output-file custom_results.json
        """
    )
    
    parser.add_argument(
        '--excel-file', 
        required=True, 
        help='语种语料 Excel 文件路径（如：语种语料 V2.xlsx）'
    )
    parser.add_argument(
        '--model-a-url', 
        default=None, 
        help='大模型 A 的 API URL（用于翻译：源语言→中文）'
    )
    parser.add_argument(
        '--model-b-url', 
        default=None,
        help='大模型 B 的 API URL（用于评分，可选）'
    )
    parser.add_argument(
        '--output-file', 
        default='reverse_translation_results.json',
        help='结果输出文件名（默认：reverse_translation_results.json）'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式：只检查数据结构，不执行翻译'
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=1,
        help='模型请求的并发数（默认：1）'
    )
    parser.add_argument(
        '--translate-model',
        type=str,
        default=None,
        help='用于翻译步骤的模型名'
    )
    parser.add_argument(
        '--evaluate-model',
        type=str,
        default=None,
        help='用于评估步骤的模型名'
    )
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = ReverseTranslationEvaluator(
        model_a_url=args.model_a_url,
        model_b_url=args.model_b_url,
        excel_file=args.excel_file,
        concurrency=args.concurrency,
        translate_model=args.translate_model,
        evaluate_model=args.evaluate_model
    )
    
    try:
        # 调试模式：只检查数据结构
        if args.debug:
            logger.info("="*80)
            logger.info("调试模式：检查 Excel 数据结构")
            logger.info("="*80)
            
            data = evaluator.read_excel_data()
            
            # 检查每个素材的语种覆盖情况
            logger.info("\n" + "="*80)
            logger.info("各素材的语种覆盖统计:")
            logger.info("="*80)
            
            for material_id in sorted(data['index'].keys()):
                languages_with_text = []
                languages_without_text = []
                
                # 新的数据结构：data['source_texts'][material_id][language]
                if material_id in data['source_texts']:
                    languages_dict = data['source_texts'][material_id]
                    for lang, text in languages_dict.items():
                        if text and len(str(text).strip()) > 0:
                            languages_with_text.append(lang)
                        else:
                            languages_without_text.append(f"{lang}(空)")
                else:
                    languages_without_text.append("无数据")
                
                logger.info(f"\n素材 {material_id}:")
                logger.info(f"  有文本的语种 ({len(languages_with_text)}): {', '.join(languages_with_text[:5])}...")
                if languages_without_text:
                    logger.info(f"  无文本的语种 ({len(languages_without_text)}): {', '.join(languages_without_text[:5])}...")
            
            return
        
        # 正常模式：执行完整评估
        # 运行评估
        results = evaluator.run_evaluation()
        
        # 保存结果
        evaluator.save_results(args.output_file)
        
        # 打印摘要
        evaluator.print_summary()
        
    except Exception as e:
        logger.error(f"✗ 评估过程发生错误：{e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
