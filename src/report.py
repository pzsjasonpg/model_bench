import json
import csv
import os
from typing import Dict, Any, Optional

class ReportGenerator:
    """结果报告生成器"""
    
    def generate_json(self, metrics: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """生成JSON格式报告"""
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            return f"报告已保存到: {output_file}"
        else:
            return json.dumps(metrics, indent=2, ensure_ascii=False)
    
    def generate_csv(self, metrics: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """生成CSV格式报告"""
        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['指标', '值'])
                for key, value in metrics.items():
                    writer.writerow([key, value])
            return f"报告已保存到: {output_file}"
        else:
            # 返回CSV格式字符串
            csv_content = '指标,值\n'
            for key, value in metrics.items():
                csv_content += f"{key},{value}\n"
            return csv_content
    
    def generate_text(self, metrics: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """生成文本格式报告"""
        report = "模型性能测试报告\n"
        report += "=" * 60 + "\n"
        for key, value in metrics.items():
            if isinstance(value, float):
                report += f"{key}: {value:.4f}\n"
            else:
                report += f"{key}: {value}\n"
        report += "=" * 60
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            return f"报告已保存到: {output_file}"
        else:
            return report
    
    def generate_report(self, metrics: Dict[str, Any], format: str = 'text', output_file: Optional[str] = None) -> str:
        """生成报告"""
        if format == 'json':
            return self.generate_json(metrics, output_file)
        elif format == 'csv':
            return self.generate_csv(metrics, output_file)
        elif format == 'text':
            return self.generate_text(metrics, output_file)
        else:
            raise ValueError(f"不支持的报告格式: {format}")