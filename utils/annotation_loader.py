"""
标注数据加载器 (Annotation Data Loader)
用于加载和管理所有需要人工标注的数据
"""

import json
import os
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AnnotationDataLoader:
    """标注数据加载器"""
    
    def __init__(self, annotation_data_path: str = "poet_annotation_data.json"):
        """
        初始化标注数据加载器
        
        Args:
            annotation_data_path: 标注数据文件路径
        """
        self.annotation_data_path = annotation_data_path
        self.annotation_data = self._load_annotation_data()
    
    def _load_annotation_data(self) -> Dict[str, Any]:
        """加载标注数据"""
        if not os.path.exists(self.annotation_data_path):
            logger.warning(f"标注数据文件不存在: {self.annotation_data_path}")
            return self._get_default_annotation_data()
        
        try:
            with open(self.annotation_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功加载标注数据: {self.annotation_data_path}")
            return data
        except Exception as e:
            logger.error(f"加载标注数据失败: {e}")
            return self._get_default_annotation_data()
    
    def _get_default_annotation_data(self) -> Dict[str, Any]:
        """获取默认标注数据（作为fallback）"""
        return {
            "domain_expert_annotations": {
                "domains": {
                    "general": {
                        "expert_time_hours": 2.0,
                        "expert_hourly_rate_usd": 100.0
                    }
                }
            },
            "task_type_annotations": {
                "task_types": {
                    "analysis_task": {
                        "expert_time_hours": 2.0
                    }
                }
            },
            "complexity_level_annotations": {
                "complexity_levels": {
                    "3": {
                        "name": "complex",
                        "description": "复杂任务"
                    }
                }
            },
            "expert_type_annotations": {
                "expert_types": {
                    "senior_analyst": {
                        "hourly_rate_usd": 100.0
                    }
                }
            },
            "token_pricing_annotations": {
                "pricing_models": {
                    "default": {
                        "input_cost_per_1k": 0.0015,
                        "output_cost_per_1k": 0.006
                    }
                }
            }
        }
    
    def get_domain_expert_data(self, domain: str) -> Tuple[float, float]:
        """
        获取指定领域的专家时间和时薪
        
        Args:
            domain: 领域名称
            
        Returns:
            (expert_time_hours, expert_hourly_rate_usd)
        """
        domains = self.annotation_data.get("domain_expert_annotations", {}).get("domains", {})
        domain_data = domains.get(domain, domains.get("general", {}))
        
        expert_time = domain_data.get("expert_time_hours", 2.0)
        expert_rate = domain_data.get("expert_hourly_rate_usd", 100.0)
        
        return expert_time, expert_rate
    
    def get_task_type_expert_time(self, task_type: str) -> float:
        """
        获取指定任务类型的专家时间
        
        Args:
            task_type: 任务类型
            
        Returns:
            expert_time_hours
        """
        task_types = self.annotation_data.get("task_type_annotations", {}).get("task_types", {})
        task_data = task_types.get(task_type, {})
        
        return task_data.get("expert_time_hours", 2.0)
    
    def get_expert_type_rate(self, expert_type: str) -> float:
        """
        获取指定专家类型的时薪
        
        Args:
            expert_type: 专家类型
            
        Returns:
            hourly_rate_usd
        """
        expert_types = self.annotation_data.get("expert_type_annotations", {}).get("expert_types", {})
        expert_data = expert_types.get(expert_type, {})
        
        return expert_data.get("hourly_rate_usd", 100.0)
    
    def get_token_pricing(self, model_name: str = "default") -> Tuple[float, float]:
        """
        获取指定模型的token定价
        
        Args:
            model_name: 模型名称
            
        Returns:
            (input_cost_per_1k, output_cost_per_1k)
        """
        pricing_models = self.annotation_data.get("token_pricing_annotations", {}).get("pricing_models", {})
        model_data = pricing_models.get(model_name, pricing_models.get("default", {}))
        
        input_cost = model_data.get("input_cost_per_1k", 0.0015)
        output_cost = model_data.get("output_cost_per_1k", 0.006)
        
        return input_cost, output_cost
    
    def get_complexity_level_info(self, level: int) -> Dict[str, Any]:
        """
        获取复杂度级别信息
        
        Args:
            level: 复杂度级别 (1-5)
            
        Returns:
            复杂度级别信息字典
        """
        complexity_levels = self.annotation_data.get("complexity_level_annotations", {}).get("complexity_levels", {})
        level_data = complexity_levels.get(str(level), {})
        
        return {
            "name": level_data.get("name", "unknown"),
            "description": level_data.get("description", ""),
            "characteristics": level_data.get("characteristics", []),
            "typical_time_range": level_data.get("typical_time_range", "")
        }
    
    def get_evaluation_thresholds(self) -> Dict[str, float]:
        """
        获取评估阈值
        
        Returns:
            评估阈值字典
        """
        thresholds = self.annotation_data.get("evaluation_thresholds_annotations", {}).get("thresholds", {})
        
        return {
            "excellent": thresholds.get("excellent_poet_score", 0.8),
            "good": thresholds.get("good_poet_score", 0.6),
            "acceptable": thresholds.get("acceptable_poet_score", 0.4),
            "poor": thresholds.get("poor_poet_score", 0.2)
        }
    
    def get_all_domains(self) -> list:
        """获取所有支持的领域列表"""
        domains = self.annotation_data.get("domain_expert_annotations", {}).get("domains", {})
        return list(domains.keys())
    
    def get_all_task_types(self) -> list:
        """获取所有支持的任务类型列表"""
        task_types = self.annotation_data.get("task_type_annotations", {}).get("task_types", {})
        return list(task_types.keys())
    
    def get_all_expert_types(self) -> list:
        """获取所有支持的专家类型列表"""
        expert_types = self.annotation_data.get("expert_type_annotations", {}).get("expert_types", {})
        return list(expert_types.keys())
    
    def get_annotation_metadata(self) -> Dict[str, Any]:
        """获取标注数据元信息"""
        return self.annotation_data.get("metadata", {})
    
    def reload_annotation_data(self):
        """重新加载标注数据"""
        self.annotation_data = self._load_annotation_data()
        logger.info("标注数据已重新加载")
    
    def validate_annotation_data(self) -> bool:
        """验证标注数据的完整性"""
        required_sections = [
            "domain_expert_annotations",
            "task_type_annotations", 
            "complexity_level_annotations",
            "expert_type_annotations",
            "token_pricing_annotations"
        ]
        
        for section in required_sections:
            if section not in self.annotation_data:
                logger.error(f"缺少必需的标注数据部分: {section}")
                return False
        
        # 验证领域数据
        domains = self.annotation_data.get("domain_expert_annotations", {}).get("domains", {})
        if not domains:
            logger.error("缺少领域专家数据")
            return False
        
        # 验证每个领域都有必需字段
        for domain, data in domains.items():
            if "expert_time_hours" not in data or "expert_hourly_rate_usd" not in data:
                logger.error(f"领域 {domain} 缺少必需字段")
                return False
        
        logger.info("标注数据验证通过")
        return True

# 全局标注数据加载器实例
annotation_loader = AnnotationDataLoader()

def get_annotation_loader() -> AnnotationDataLoader:
    """获取全局标注数据加载器实例"""
    return annotation_loader
