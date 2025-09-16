"""
数据格式验证和转换工具 (Data Format Validation and Conversion Tools)
用于验证和转换不同版本的输入数据格式
"""

import json
import jsonschema
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DataFormatValidator:
    """数据格式验证器"""

    def __init__(self, schema_path: str = "data_schemas/web_interaction_data_schema.json"):
        """
        初始化数据格式验证器

        Args:
            schema_path: JSON Schema文件路径
        """
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """加载JSON Schema"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
                return schema_data.get("schema", {})
        except FileNotFoundError:
            logger.error(f"Schema文件未找到: {self.schema_path}")
            return self._get_default_schema()
        except Exception as e:
            logger.error(f"加载Schema失败: {e}")
            return self._get_default_schema()

    def _get_default_schema(self) -> Dict[str, Any]:
        """获取默认的简化Schema"""
        return {
            "type": "object",
            "required": ["id", "prompt", "article"],
            "properties": {
                "id": {"type": ["integer", "string"]},
                "prompt": {"type": "string"},
                "article": {"type": "string"},
                "interaction_metrics": {"type": "object"}
            }
        }

    def validate_single_record(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证单条记录

        Args:
            data: 待验证的数据记录

        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        try:
            jsonschema.validate(instance=data, schema=self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"数据验证失败: {e.message}")
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")

        return False, errors

    def validate_dataset(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证整个数据集

        Args:
            data: 数据集（记录列表）

        Returns:
            Dict[str, Any]: 验证报告
        """
        total_records = len(data)
        valid_records = 0
        invalid_records = []
        validation_errors = []

        for i, record in enumerate(data):
            is_valid, errors = self.validate_single_record(record)

            if is_valid:
                valid_records += 1
            else:
                invalid_records.append({
                    "index": i,
                    "id": record.get("id", "unknown"),
                    "errors": errors
                })
                validation_errors.extend([f"记录 {i}: {error}" for error in errors])

        report = {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": len(invalid_records),
            "validation_success_rate": valid_records / total_records if total_records > 0 else 0,
            "invalid_record_details": invalid_records,
            "summary_errors": validation_errors[:10]  # 只显示前10个错误
        }

        return report

class DataFormatConverter:
    """数据格式转换器"""

    def __init__(self):
        """初始化数据格式转换器"""
        pass

    def detect_format_version(self, data: Dict[str, Any]) -> str:
        """
        检测数据格式版本

        Args:
            data: 数据记录

        Returns:
            str: 数据格式版本 ('legacy', 'web_interaction', 'unknown')
        """
        required_legacy_fields = {"id", "prompt", "article"}
        has_legacy_fields = all(field in data for field in required_legacy_fields)

        if "interaction_metrics" in data and has_legacy_fields:
            return "web_interaction"
        elif has_legacy_fields:
            return "legacy"
        else:
            return "unknown"

    def convert_legacy_to_web_interaction(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将传统格式数据转换为Web交互格式

        Args:
            legacy_data: 传统格式数据

        Returns:
            Dict[str, Any]: Web交互格式数据
        """
        # 基础字段
        converted_data = {
            "id": legacy_data.get("id"),
            "prompt": legacy_data.get("prompt", ""),
            "article": legacy_data.get("article", "")
        }

        # 估算交互指标
        article_text = legacy_data.get("article", "")
        prompt_text = legacy_data.get("prompt", "")

        word_count = len(article_text.split())
        prompt_word_count = len(prompt_text.split())

        # 估算时间（基于内容长度）
        estimated_duration = max(60, word_count * 0.5)  # 每词0.5秒
        thinking_time = min(estimated_duration * 0.1, 30)  # 不超过30秒
        first_response = min(5.0, thinking_time)

        # 估算token数量
        estimated_input_tokens = int(prompt_word_count * 1.3)
        estimated_output_tokens = int(word_count * 1.3)

        # 估算成本（使用Claude-3-sonnet默认定价）
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        estimated_cost = (estimated_input_tokens / 1000) * input_cost_per_1k + \
                        (estimated_output_tokens / 1000) * output_cost_per_1k

        # 创建interaction_metrics
        converted_data["interaction_metrics"] = {
            "timing": {
                "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_time": (datetime.now()).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total_duration_seconds": estimated_duration,
                "thinking_time_seconds": thinking_time,
                "first_response_time_seconds": first_response,
                "interaction_phases": [
                    {
                        "phase_name": "content_generation",
                        "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "duration_seconds": estimated_duration
                    }
                ]
            },
            "token_usage": {
                "total_input_tokens": estimated_input_tokens,
                "total_output_tokens": estimated_output_tokens,
                "prompt_tokens": estimated_input_tokens,
                "reasoning_tokens": 0,
                "tool_call_tokens": 0,
                "model_name": "estimated-model",
                "estimated_cost_usd": estimated_cost
            },
            "interaction_details": {
                "tool_calls": [
                    {
                        "tool_name": "WebSearch",
                        "call_count": 3,
                        "total_duration_seconds": estimated_duration * 0.3,
                        "success_rate": 0.9,
                        "parameters_used": ["query"]
                    }
                ],
                "search_queries": [
                    {
                        "query_text": "estimated query",
                        "results_count": 10,
                        "relevance_score": 0.8
                    }
                ],
                "user_feedback": {
                    "interruptions": 0,
                    "clarifications_requested": 0,
                    "satisfaction_rating": 3.5
                }
            },
            "performance_metrics": {
                "automation_rate": 0.8,
                "error_rate": 0.05,
                "retry_count": 0,
                "efficiency_score": 0.75,
                "resource_utilization": {
                    "memory_usage_mb": 256,
                    "cpu_usage_percent": 40,
                    "network_requests": 5
                }
            }
        }

        # 添加任务元数据
        converted_data["task_metadata"] = {
            "domain": "general",
            "task_type": "analysis_task",
            "complexity_level": 3,
            "user_id": "unknown",
            "session_id": "legacy_conversion",
            "tags": ["converted_from_legacy"]
        }

        # 添加质量指标
        converted_data["quality_metrics"] = {
            "content_length": {
                "word_count": word_count,
                "paragraph_count": article_text.count('\n\n') + 1,
                "citation_count": article_text.count('[') if '[' in article_text else 0
            },
            "information_coverage": {
                "sources_used": max(1, article_text.count('http')),
                "unique_facts": max(1, word_count // 100),  # 估算
                "coverage_completeness": 0.75
            }
        }

        return converted_data

    def convert_dataset(self, input_data: List[Dict[str, Any]],
                       target_format: str = "web_interaction") -> List[Dict[str, Any]]:
        """
        转换整个数据集

        Args:
            input_data: 输入数据集
            target_format: 目标格式

        Returns:
            List[Dict[str, Any]]: 转换后的数据集
        """
        converted_data = []
        conversion_stats = {"converted": 0, "skipped": 0, "errors": 0}

        for i, record in enumerate(input_data):
            try:
                source_format = self.detect_format_version(record)

                if source_format == target_format:
                    converted_data.append(record)
                    conversion_stats["skipped"] += 1
                elif source_format == "legacy" and target_format == "web_interaction":
                    converted_record = self.convert_legacy_to_web_interaction(record)
                    converted_data.append(converted_record)
                    conversion_stats["converted"] += 1
                else:
                    logger.warning(f"无法转换记录 {i}: {source_format} -> {target_format}")
                    converted_data.append(record)  # 保持原样
                    conversion_stats["errors"] += 1
            except Exception as e:
                logger.error(f"转换记录 {i} 时发生错误: {e}")
                converted_data.append(record)  # 保持原样
                conversion_stats["errors"] += 1

        logger.info(f"数据集转换完成: {conversion_stats}")
        return converted_data

class DataFormatManager:
    """数据格式管理器"""

    def __init__(self, schema_path: str = "data_schemas/web_interaction_data_schema.json"):
        """
        初始化数据格式管理器

        Args:
            schema_path: Schema文件路径
        """
        self.validator = DataFormatValidator(schema_path)
        self.converter = DataFormatConverter()

    def process_jsonl_file(self, input_file: str, output_file: str = None,
                          validate_only: bool = False,
                          convert_to_web_interaction: bool = False) -> Dict[str, Any]:
        """
        处理JSONL文件

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（如果不指定，则基于输入文件名生成）
            validate_only: 仅验证，不转换
            convert_to_web_interaction: 是否转换为web_interaction格式

        Returns:
            Dict[str, Any]: 处理报告
        """
        try:
            # 读取数据
            with open(input_file, 'r', encoding='utf-8') as f:
                data = [json.loads(line.strip()) for line in f if line.strip()]

            logger.info(f"加载了 {len(data)} 条记录")

            # 验证数据
            validation_report = self.validator.validate_dataset(data)
            logger.info(f"验证结果: {validation_report['valid_records']}/{validation_report['total_records']} 条记录有效")

            result = {
                "input_file": input_file,
                "total_records": len(data),
                "validation_report": validation_report,
                "processing_completed": True
            }

            if validate_only:
                return result

            # 转换数据（如果需要）
            if convert_to_web_interaction:
                logger.info("开始转换数据格式...")
                converted_data = self.converter.convert_dataset(data, "web_interaction")

                # 再次验证转换后的数据
                post_conversion_validation = self.validator.validate_dataset(converted_data)
                result["post_conversion_validation"] = post_conversion_validation

                data = converted_data

            # 保存结果
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                suffix = "_web_interaction" if convert_to_web_interaction else "_validated"
                output_file = f"{base_name}{suffix}.jsonl"

            with open(output_file, 'w', encoding='utf-8') as f:
                for record in data:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

            result["output_file"] = output_file
            logger.info(f"处理完成，结果保存到: {output_file}")

            return result

        except Exception as e:
            logger.error(f"处理文件时发生错误: {e}")
            return {
                "input_file": input_file,
                "error": str(e),
                "processing_completed": False
            }

    def generate_sample_web_interaction_data(self, output_file: str = "sample_web_interaction_data.jsonl",
                                           num_samples: int = 3) -> str:
        """
        生成示例Web交互数据文件

        Args:
            output_file: 输出文件路径
            num_samples: 生成样本数量

        Returns:
            str: 输出文件路径
        """
        samples = []

        for i in range(num_samples):
            sample = {
                "id": i + 1,
                "prompt": f"这是第 {i+1} 个示例查询，用于演示Web交互数据格式",
                "article": f"这是第 {i+1} 个示例回答。" + "内容详细展示了AI智能体的回答能力。" * 10,
                "interaction_metrics": {
                    "timing": {
                        "start_time": "2024-01-01T10:00:00Z",
                        "end_time": "2024-01-01T10:15:30Z",
                        "total_duration_seconds": 930 + i * 100,
                        "thinking_time_seconds": 45 + i * 5,
                        "first_response_time_seconds": 3.2,
                        "interaction_phases": [
                            {
                                "phase_name": "initial_search",
                                "start_time": "2024-01-01T10:00:00Z",
                                "duration_seconds": 120
                            },
                            {
                                "phase_name": "content_generation",
                                "start_time": "2024-01-01T10:02:00Z",
                                "duration_seconds": 810 + i * 100
                            }
                        ]
                    },
                    "token_usage": {
                        "total_input_tokens": 1500 + i * 200,
                        "total_output_tokens": 8500 + i * 1000,
                        "prompt_tokens": 150 + i * 20,
                        "reasoning_tokens": 1350 + i * 180,
                        "tool_call_tokens": 200,
                        "model_name": "claude-3-7-sonnet-latest",
                        "estimated_cost_usd": 0.045 + i * 0.01
                    },
                    "interaction_details": {
                        "tool_calls": [
                            {
                                "tool_name": "WebSearch",
                                "call_count": 8 + i,
                                "total_duration_seconds": 240,
                                "success_rate": 0.875 + i * 0.02,
                                "parameters_used": ["query", "max_results"]
                            }
                        ],
                        "search_queries": [
                            {
                                "query_text": f"示例搜索查询 {i+1}",
                                "results_count": 25 + i * 5,
                                "relevance_score": 0.85 + i * 0.03
                            }
                        ],
                        "user_feedback": {
                            "interruptions": 0,
                            "clarifications_requested": 0,
                            "satisfaction_rating": 4.5 - i * 0.1
                        }
                    },
                    "performance_metrics": {
                        "automation_rate": 0.95 - i * 0.02,
                        "error_rate": 0.02 + i * 0.005,
                        "retry_count": i,
                        "efficiency_score": 0.88 - i * 0.05,
                        "resource_utilization": {
                            "memory_usage_mb": 512 + i * 100,
                            "cpu_usage_percent": 45 + i * 5,
                            "network_requests": 13 + i * 2
                        }
                    }
                },
                "task_metadata": {
                    "domain": ["research", "technology", "finance"][i % 3],
                    "task_type": ["research_task", "analysis_task", "complex_research"][i % 3],
                    "complexity_level": 3 + i,
                    "user_id": f"user_{100 + i}",
                    "session_id": f"session_{400 + i}",
                    "tags": [f"标签{i+1}", "示例", "测试"]
                },
                "quality_metrics": {
                    "content_length": {
                        "word_count": 12500 + i * 1000,
                        "paragraph_count": 45 + i * 5,
                        "citation_count": 16 + i * 2
                    },
                    "information_coverage": {
                        "sources_used": 16 + i * 2,
                        "unique_facts": 35 + i * 5,
                        "coverage_completeness": 0.92 - i * 0.05
                    }
                }
            }
            samples.append(sample)

        # 保存样本数据
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info(f"生成了 {num_samples} 个Web交互数据样本，保存到: {output_file}")
        return output_file

def main():
    """命令行工具主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据格式验证和转换工具')
    parser.add_argument('--input_file', required=True, help='输入JSONL文件路径')
    parser.add_argument('--output_file', help='输出文件路径（可选）')
    parser.add_argument('--validate_only', action='store_true', help='仅验证数据，不转换')
    parser.add_argument('--convert', action='store_true', help='转换为Web交互格式')
    parser.add_argument('--generate_sample', action='store_true', help='生成示例数据文件')
    parser.add_argument('--schema_path', default='data_schemas/web_interaction_data_schema.json',
                       help='Schema文件路径')

    args = parser.parse_args()

    manager = DataFormatManager(args.schema_path)

    if args.generate_sample:
        output_file = args.output_file or "sample_web_interaction_data.jsonl"
        manager.generate_sample_web_interaction_data(output_file)
        return

    # 处理输入文件
    report = manager.process_jsonl_file(
        input_file=args.input_file,
        output_file=args.output_file,
        validate_only=args.validate_only,
        convert_to_web_interaction=args.convert
    )

    # 打印报告
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()