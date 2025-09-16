"""
增强的标注数据加载器 (Enhanced Annotation Data Loader)
用于加载和管理分散在多个文件中的标注数据
"""

import json
import os
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class EnhancedAnnotationLoader:
    """增强的标注数据加载器，支持分文件存储"""

    def __init__(self, annotation_base_dir: str = "data/annotation"):
        """
        初始化增强标注数据加载器

        Args:
            annotation_base_dir: 标注数据文件目录
        """
        self.annotation_base_dir = annotation_base_dir
        self.annotation_files = {
            "domain_expert": "domain_expert_data.json",
            "task_type": "task_type_data.json",
            "expert_type": "expert_type_data.json",
            "token_pricing": "token_pricing_data.json",
            "complexity_level": "complexity_level_data.json"
        }

        self.data_cache = {}
        self._load_all_annotation_data()

    def _load_all_annotation_data(self):
        """加载所有标注数据文件"""
        for data_type, filename in self.annotation_files.items():
            file_path = os.path.join(self.annotation_base_dir, filename)
            self.data_cache[data_type] = self._load_single_file(file_path, data_type)

    def _load_single_file(self, file_path: str, data_type: str) -> Dict[str, Any]:
        """加载单个标注数据文件"""
        if not os.path.exists(file_path):
            logger.warning(f"标注数据文件不存在: {file_path}")
            return self._get_default_data(data_type)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载标注数据: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载标注数据失败 {file_path}: {e}")
            return self._get_default_data(data_type)

    def _get_default_data(self, data_type: str) -> Dict[str, Any]:
        """获取默认标注数据"""
        defaults = {
            "domain_expert": {
                "domains": {
                    "general": {
                        "expert_time_hours": 2.0,
                        "expert_hourly_rate_usd": 100.0,
                        "description": "通用任务默认设置"
                    }
                }
            },
            "task_type": {
                "task_types": {
                    "analysis_task": {
                        "expert_time_hours": 2.0,
                        "description": "默认分析任务"
                    }
                }
            },
            "expert_type": {
                "expert_types": {
                    "senior_analyst": {
                        "hourly_rate_usd": 100.0,
                        "description": "默认专家类型"
                    }
                }
            },
            "token_pricing": {
                "pricing_models": {
                    "default": {
                        "input_cost_per_1k": 0.0015,
                        "output_cost_per_1k": 0.006,
                        "description": "默认token定价"
                    }
                }
            },
            "complexity_level": {
                "complexity_levels": {
                    "3": {
                        "name": "complex",
                        "description": "默认复杂度级别"
                    }
                },
                "complexity_mapping": {
                    "simple": 1,
                    "moderate": 2,
                    "complex": 3,
                    "advanced": 4,
                    "expert": 5
                }
            }
        }
        return defaults.get(data_type, {})

    def get_domain_expert_data(self, domain: str) -> Tuple[float, float]:
        """
        获取指定领域的专家时间和时薪

        Args:
            domain: 领域名称

        Returns:
            (expert_time_hours, expert_hourly_rate_usd)
        """
        domain_data = self.data_cache.get("domain_expert", {})
        domains = domain_data.get("domains", {})

        # 优先使用指定领域，回退到general
        target_domain = domains.get(domain, domains.get("general", {}))

        expert_time = target_domain.get("expert_time_hours", 2.0)
        expert_rate = target_domain.get("expert_hourly_rate_usd", 100.0)

        return expert_time, expert_rate

    def get_task_type_expert_time(self, task_type: str) -> float:
        """
        获取指定任务类型的专家时间

        Args:
            task_type: 任务类型

        Returns:
            expert_time_hours
        """
        task_data = self.data_cache.get("task_type", {})
        task_types = task_data.get("task_types", {})

        task_info = task_types.get(task_type, {})
        return task_info.get("expert_time_hours", 2.0)

    def get_expert_type_rate(self, expert_type: str) -> float:
        """
        获取指定专家类型的时薪

        Args:
            expert_type: 专家类型

        Returns:
            hourly_rate_usd
        """
        expert_data = self.data_cache.get("expert_type", {})
        expert_types = expert_data.get("expert_types", {})

        expert_info = expert_types.get(expert_type, {})
        return expert_info.get("hourly_rate_usd", 100.0)

    def get_token_pricing(self, model_name: str = "default") -> Tuple[float, float]:
        """
        获取指定模型的token定价

        Args:
            model_name: 模型名称

        Returns:
            (input_cost_per_1k, output_cost_per_1k)
        """
        pricing_data = self.data_cache.get("token_pricing", {})
        pricing_models = pricing_data.get("pricing_models", {})

        # 优先使用指定模型，回退到default
        model_info = pricing_models.get(model_name, pricing_models.get("default", {}))

        input_cost = model_info.get("input_cost_per_1k", 0.0015)
        output_cost = model_info.get("output_cost_per_1k", 0.006)

        return input_cost, output_cost

    def get_complexity_level_info(self, level: int) -> Dict[str, Any]:
        """
        获取复杂度级别信息

        Args:
            level: 复杂度级别 (1-5)

        Returns:
            复杂度级别信息字典
        """
        complexity_data = self.data_cache.get("complexity_level", {})
        complexity_levels = complexity_data.get("complexity_levels", {})

        level_info = complexity_levels.get(str(level), {})

        return {
            "name": level_info.get("name", "unknown"),
            "description": level_info.get("description", ""),
            "characteristics": level_info.get("characteristics", []),
            "typical_time_range": level_info.get("typical_time_range", ""),
            "example_tasks": level_info.get("example_tasks", [])
        }

    def get_complexity_mapping(self) -> Dict[str, int]:
        """获取复杂度映射"""
        complexity_data = self.data_cache.get("complexity_level", {})
        return complexity_data.get("complexity_mapping", {
            "simple": 1,
            "moderate": 2,
            "complex": 3,
            "advanced": 4,
            "expert": 5
        })

    def get_all_domains(self) -> List[str]:
        """获取所有支持的领域列表"""
        domain_data = self.data_cache.get("domain_expert", {})
        domains = domain_data.get("domains", {})
        return list(domains.keys())

    def get_all_task_types(self) -> List[str]:
        """获取所有支持的任务类型列表"""
        task_data = self.data_cache.get("task_type", {})
        task_types = task_data.get("task_types", {})
        return list(task_types.keys())

    def get_all_expert_types(self) -> List[str]:
        """获取所有支持的专家类型列表"""
        expert_data = self.data_cache.get("expert_type", {})
        expert_types = expert_data.get("expert_types", {})
        return list(expert_types.keys())

    def get_all_token_models(self) -> List[str]:
        """获取所有支持的token定价模型列表"""
        pricing_data = self.data_cache.get("token_pricing", {})
        pricing_models = pricing_data.get("pricing_models", {})
        return list(pricing_models.keys())

    def get_annotation_metadata(self) -> Dict[str, Dict[str, Any]]:
        """获取所有标注数据元信息"""
        metadata = {}
        for data_type, data in self.data_cache.items():
            metadata[data_type] = {
                "version": data.get("version", "unknown"),
                "last_updated": data.get("last_updated", "unknown"),
                "description": data.get("description", "")
            }
        return metadata

    def reload_annotation_data(self):
        """重新加载所有标注数据"""
        self.data_cache.clear()
        self._load_all_annotation_data()
        logger.info("所有标注数据已重新加载")

    def validate_annotation_data(self) -> bool:
        """验证标注数据的完整性"""
        required_data_types = ["domain_expert", "task_type", "expert_type", "token_pricing", "complexity_level"]

        for data_type in required_data_types:
            if data_type not in self.data_cache:
                logger.error(f"缺少必需的标注数据类型: {data_type}")
                return False

        # 验证领域数据
        domain_data = self.data_cache.get("domain_expert", {})
        domains = domain_data.get("domains", {})
        if not domains:
            logger.error("缺少领域专家数据")
            return False

        # 验证每个领域都有必需字段
        for domain, data in domains.items():
            if "expert_time_hours" not in data or "expert_hourly_rate_usd" not in data:
                logger.error(f"领域 {domain} 缺少必需字段")
                return False

        # 验证任务类型数据
        task_data = self.data_cache.get("task_type", {})
        task_types = task_data.get("task_types", {})
        if not task_types:
            logger.error("缺少任务类型数据")
            return False

        # 验证专家类型数据
        expert_data = self.data_cache.get("expert_type", {})
        expert_types = expert_data.get("expert_types", {})
        if not expert_types:
            logger.error("缺少专家类型数据")
            return False

        # 验证token定价数据
        pricing_data = self.data_cache.get("token_pricing", {})
        pricing_models = pricing_data.get("pricing_models", {})
        if not pricing_models or "default" not in pricing_models:
            logger.error("缺少token定价数据或默认模型")
            return False

        # 验证复杂度级别数据
        complexity_data = self.data_cache.get("complexity_level", {})
        complexity_levels = complexity_data.get("complexity_levels", {})
        complexity_mapping = complexity_data.get("complexity_mapping", {})
        if not complexity_levels or not complexity_mapping:
            logger.error("缺少复杂度级别数据")
            return False

        logger.info("所有标注数据验证通过")
        return True

    def get_data_statistics(self) -> Dict[str, Any]:
        """获取标注数据统计信息"""
        stats = {}

        # 领域统计
        domain_data = self.data_cache.get("domain_expert", {})
        domains = domain_data.get("domains", {})
        stats["domains"] = {
            "count": len(domains),
            "avg_time": sum(d.get("expert_time_hours", 0) for d in domains.values()) / len(domains) if domains else 0,
            "avg_rate": sum(d.get("expert_hourly_rate_usd", 0) for d in domains.values()) / len(domains) if domains else 0
        }

        # 任务类型统计
        task_data = self.data_cache.get("task_type", {})
        task_types = task_data.get("task_types", {})
        stats["task_types"] = {
            "count": len(task_types),
            "avg_time": sum(t.get("expert_time_hours", 0) for t in task_types.values()) / len(task_types) if task_types else 0
        }

        # 专家类型统计
        expert_data = self.data_cache.get("expert_type", {})
        expert_types = expert_data.get("expert_types", {})
        stats["expert_types"] = {
            "count": len(expert_types),
            "avg_rate": sum(e.get("hourly_rate_usd", 0) for e in expert_types.values()) / len(expert_types) if expert_types else 0
        }

        # Token定价统计
        pricing_data = self.data_cache.get("token_pricing", {})
        pricing_models = pricing_data.get("pricing_models", {})
        stats["pricing_models"] = {
            "count": len(pricing_models)
        }

        # 复杂度级别统计
        complexity_data = self.data_cache.get("complexity_level", {})
        complexity_levels = complexity_data.get("complexity_levels", {})
        stats["complexity_levels"] = {
            "count": len(complexity_levels)
        }

        return stats

# 全局增强标注数据加载器实例
enhanced_annotation_loader = EnhancedAnnotationLoader()

def get_enhanced_annotation_loader() -> EnhancedAnnotationLoader:
    """获取全局增强标注数据加载器实例"""
    return enhanced_annotation_loader