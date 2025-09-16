"""
Web交互数据评估器 (Web Interaction Data Evaluator)
直接从JSON数据中读取实际的交互指标，用于POET评估
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from .enhanced_annotation_loader import EnhancedAnnotationLoader

logger = logging.getLogger(__name__)

@dataclass
class WebInteractionMetrics:
    """从Web UI交互中提取的实际指标"""
    task_id: str
    task_title: str

    # 时间相关指标（从JSON直接读取）
    total_duration_seconds: float
    thinking_time_seconds: float
    first_response_time_seconds: float

    # Token使用情况（从JSON直接读取）
    total_input_tokens: int
    total_output_tokens: int
    model_name: str
    estimated_cost_usd: float

    # 性能指标（从JSON直接读取）
    automation_rate: float
    error_rate: float
    efficiency_score: float
    retry_count: int

    # 工具使用情况（从JSON直接读取）
    tool_calls_count: int
    search_queries_count: int
    successful_tool_rate: float

    # 内容质量指标（从JSON直接读取）
    word_count: int
    citation_count: int
    sources_used: int
    coverage_completeness: float

    # 用户满意度（从JSON直接读取）
    user_satisfaction_rating: float
    user_interruptions: int

    # 专家基准对比数据（从标注数据获取）
    expert_time_hours: float
    expert_hourly_rate_usd: float

    # 计算得出的对比指标
    time_savings_hours: float
    cost_saving_usd: float
    efficiency_vs_expert: float

class WebInteractionEvaluator:
    """Web交互数据评估器 - 从JSON读取真实指标而不是计算"""

    def __init__(self, annotation_base_dir: str = "data/annotation"):
        """
        初始化Web交互评估器

        Args:
            annotation_base_dir: 标注数据目录
        """
        self.annotation_loader = EnhancedAnnotationLoader(annotation_base_dir)

    def extract_interaction_metrics(self, task_data: Dict[str, Any]) -> WebInteractionMetrics:
        """
        从Web UI交互数据中提取所有指标

        Args:
            task_data: 包含interaction_metrics的完整任务数据

        Returns:
            WebInteractionMetrics: 提取的交互指标
        """
        task_id = str(task_data["id"])
        task_title = task_data.get("title", "")

        # 检查是否包含交互指标
        if "interaction_metrics" not in task_data:
            logger.warning(f"任务 {task_id} 缺少 interaction_metrics 数据，使用默认值")
            return self._create_default_metrics(task_id, task_title, task_data)

        interaction_metrics = task_data["interaction_metrics"]

        # 从JSON中直接提取时间指标
        timing = interaction_metrics.get("timing", {})
        total_duration_seconds = timing.get("total_duration_seconds", 0.0)
        thinking_time_seconds = timing.get("thinking_time_seconds", 0.0)
        first_response_time_seconds = timing.get("first_response_time_seconds", 0.0)

        # 从JSON中直接提取token使用情况
        token_usage = interaction_metrics.get("token_usage", {})
        total_input_tokens = token_usage.get("total_input_tokens", 0)
        total_output_tokens = token_usage.get("total_output_tokens", 0)
        model_name = token_usage.get("model_name", "unknown")
        estimated_cost_usd = token_usage.get("estimated_cost_usd", 0.0)

        # 从JSON中直接提取性能指标
        performance_metrics = interaction_metrics.get("performance_metrics", {})
        automation_rate = performance_metrics.get("automation_rate", 0.0)
        error_rate = performance_metrics.get("error_rate", 0.0)
        efficiency_score = performance_metrics.get("efficiency_score", 0.0)
        retry_count = performance_metrics.get("retry_count", 0)

        # 从JSON中提取工具使用情况
        interaction_details = interaction_metrics.get("interaction_details", {})
        tool_calls = interaction_details.get("tool_calls", [])
        search_queries = interaction_details.get("search_queries", [])

        tool_calls_count = sum(tool.get("call_count", 0) for tool in tool_calls)
        search_queries_count = len(search_queries)

        # 计算工具成功率
        if tool_calls:
            successful_tool_rate = sum(tool.get("success_rate", 0) for tool in tool_calls) / len(tool_calls)
        else:
            successful_tool_rate = 1.0

        # 从JSON中提取用户反馈
        user_feedback = interaction_details.get("user_feedback", {})
        user_satisfaction_rating = user_feedback.get("satisfaction_rating", 3.0)
        user_interruptions = user_feedback.get("interruptions", 0)

        # 从JSON中提取内容质量指标
        quality_metrics = task_data.get("quality_metrics", {})
        content_length = quality_metrics.get("content_length", {})
        information_coverage = quality_metrics.get("information_coverage", {})

        word_count = content_length.get("word_count", len(task_data.get("article", "").split()))
        citation_count = content_length.get("citation_count", 0)
        sources_used = information_coverage.get("sources_used", 0)
        coverage_completeness = information_coverage.get("coverage_completeness", 0.5)

        # 从标注数据获取专家基准
        domain = task_data.get("task_metadata", {}).get("domain", "general")
        task_type = task_data.get("task_metadata", {}).get("task_type", "analysis_task")

        expert_time, expert_rate = self.annotation_loader.get_domain_expert_data(domain)

        # 如果有具体任务类型，使用更精确的时间估算
        if task_type:
            task_type_time = self.annotation_loader.get_task_type_expert_time(task_type)
            expert_time = task_type_time

        # 计算对比指标
        ai_time_hours = total_duration_seconds / 3600
        time_savings_hours = max(0, expert_time - ai_time_hours)

        expert_cost = expert_time * expert_rate
        ai_cost = estimated_cost_usd
        cost_saving_usd = max(0, expert_cost - ai_cost)

        efficiency_vs_expert = min(1.0, expert_time / ai_time_hours) if ai_time_hours > 0 else 1.0

        return WebInteractionMetrics(
            task_id=task_id,
            task_title=task_title,
            total_duration_seconds=total_duration_seconds,
            thinking_time_seconds=thinking_time_seconds,
            first_response_time_seconds=first_response_time_seconds,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            model_name=model_name,
            estimated_cost_usd=estimated_cost_usd,
            automation_rate=automation_rate,
            error_rate=error_rate,
            efficiency_score=efficiency_score,
            retry_count=retry_count,
            tool_calls_count=tool_calls_count,
            search_queries_count=search_queries_count,
            successful_tool_rate=successful_tool_rate,
            word_count=word_count,
            citation_count=citation_count,
            sources_used=sources_used,
            coverage_completeness=coverage_completeness,
            user_satisfaction_rating=user_satisfaction_rating,
            user_interruptions=user_interruptions,
            expert_time_hours=expert_time,
            expert_hourly_rate_usd=expert_rate,
            time_savings_hours=time_savings_hours,
            cost_saving_usd=cost_saving_usd,
            efficiency_vs_expert=efficiency_vs_expert
        )

    def _create_default_metrics(self, task_id: str, task_title: str, task_data: Dict[str, Any]) -> WebInteractionMetrics:
        """
        为缺少interaction_metrics的旧格式数据创建默认指标

        Args:
            task_id: 任务ID
            task_title: 任务标题
            task_data: 任务数据

        Returns:
            WebInteractionMetrics: 默认指标
        """
        logger.warning(f"为任务 {task_id} 创建默认交互指标")

        # 基于内容长度估算指标
        article_text = task_data.get("article", "")
        prompt_text = task_data.get("prompt", "")

        word_count = len(article_text.split())
        prompt_length = len(prompt_text.split())

        # 估算时间（基于内容长度）
        estimated_duration = max(60, word_count * 0.5)  # 假设每个词0.5秒
        thinking_time = min(estimated_duration * 0.1, 30)  # 思考时间不超过30秒
        first_response_time = min(5.0, thinking_time)

        # 估算token使用
        estimated_input_tokens = int(prompt_length * 1.3)
        estimated_output_tokens = int(word_count * 1.3)

        # 基于token使用估算成本（假设使用Claude-3.5-sonnet）
        input_cost, output_cost = self.annotation_loader.get_token_pricing("claude-3-sonnet")
        estimated_cost = (estimated_input_tokens / 1000) * input_cost + (estimated_output_tokens / 1000) * output_cost

        # 设置合理的默认值
        domain = task_data.get("task_metadata", {}).get("domain", "general")
        task_type = task_data.get("task_metadata", {}).get("task_type", "analysis_task")

        expert_time, expert_rate = self.annotation_loader.get_domain_expert_data(domain)
        if task_type:
            task_type_time = self.annotation_loader.get_task_type_expert_time(task_type)
            expert_time = task_type_time

        ai_time_hours = estimated_duration / 3600
        time_savings_hours = max(0, expert_time - ai_time_hours)
        expert_cost = expert_time * expert_rate
        cost_saving_usd = max(0, expert_cost - estimated_cost)
        efficiency_vs_expert = min(1.0, expert_time / ai_time_hours) if ai_time_hours > 0 else 1.0

        return WebInteractionMetrics(
            task_id=task_id,
            task_title=task_title,
            total_duration_seconds=estimated_duration,
            thinking_time_seconds=thinking_time,
            first_response_time_seconds=first_response_time,
            total_input_tokens=estimated_input_tokens,
            total_output_tokens=estimated_output_tokens,
            model_name="estimated-model",
            estimated_cost_usd=estimated_cost,
            automation_rate=0.8,  # 默认自动化率
            error_rate=0.05,  # 默认错误率
            efficiency_score=0.7,  # 默认效率分数
            retry_count=0,
            tool_calls_count=5,  # 估算的工具调用次数
            search_queries_count=3,  # 估算的搜索次数
            successful_tool_rate=0.9,
            word_count=word_count,
            citation_count=article_text.count('[') if '[' in article_text else 0,  # 简单估算引用数
            sources_used=max(1, article_text.count('http')),  # 基于URL数量估算源数量
            coverage_completeness=0.75,  # 默认完整性
            user_satisfaction_rating=3.5,  # 默认满意度
            user_interruptions=0,
            expert_time_hours=expert_time,
            expert_hourly_rate_usd=expert_rate,
            time_savings_hours=time_savings_hours,
            cost_saving_usd=cost_saving_usd,
            efficiency_vs_expert=efficiency_vs_expert
        )

    def calculate_efficiency_metrics(self, web_metrics: WebInteractionMetrics) -> Dict[str, float]:
        """
        基于Web交互指标计算效率价值各项分数

        Args:
            web_metrics: Web交互指标

        Returns:
            Dict[str, float]: 效率价值各项分数
        """
        # 时间效率：基于与专家时间的对比
        time_efficiency = min(1.0, web_metrics.efficiency_vs_expert)

        # 成本效率：基于成本节约
        if web_metrics.expert_time_hours * web_metrics.expert_hourly_rate_usd > 0:
            expert_cost = web_metrics.expert_time_hours * web_metrics.expert_hourly_rate_usd
            cost_efficiency = min(1.0, web_metrics.cost_saving_usd / expert_cost)
        else:
            cost_efficiency = 0.5

        # 自动化效率：直接从JSON读取
        automation_efficiency = web_metrics.automation_rate

        # 质量效率：基于错误率和用户满意度
        quality_efficiency = (1.0 - web_metrics.error_rate) * (web_metrics.user_satisfaction_rating / 5.0)

        return {
            "time_efficiency": time_efficiency,
            "cost_efficiency": cost_efficiency,
            "automation_efficiency": automation_efficiency,
            "quality_efficiency": quality_efficiency,
            "overall_efficiency": (time_efficiency + cost_efficiency + automation_efficiency + quality_efficiency) / 4.0
        }

    def calculate_strategic_metrics(self, web_metrics: WebInteractionMetrics, task_data: Dict[str, Any]) -> Dict[str, float]:
        """
        基于Web交互数据计算战略价值指标

        Args:
            web_metrics: Web交互指标
            task_data: 任务数据

        Returns:
            Dict[str, float]: 战略价值各项分数
        """
        complexity_level = task_data.get("task_metadata", {}).get("complexity_level", 3)

        # 多步推理能力：基于工具调用和思考时间
        reasoning_score = min(5.0, (web_metrics.tool_calls_count / 5.0) * 2 +
                             (web_metrics.thinking_time_seconds / 60.0) * 3)

        # 领域专业度：基于信息源使用和引用质量
        domain_expertise = min(5.0, (web_metrics.sources_used / 10.0) * 3 +
                              (web_metrics.citation_count / 20.0) * 2)

        # 综合能力：基于内容质量和完整性
        synthesis_capability = min(5.0, web_metrics.coverage_completeness * 5)

        # 独立性：基于自动化率和错误率
        independence = min(5.0, web_metrics.automation_rate * (1.0 - web_metrics.error_rate) * 5)

        # 知识提取能力：基于搜索效率
        knowledge_extraction = min(5.0, web_metrics.search_queries_count / 2.0 +
                                  web_metrics.successful_tool_rate * 3)

        # 知识组织能力：基于内容结构
        knowledge_organization = min(5.0, (web_metrics.word_count / 5000.0) * 3 +
                                    (web_metrics.coverage_completeness * 2))

        # 知识复用潜力：基于引用和源的使用
        knowledge_reuse = min(5.0, (web_metrics.citation_count / 15.0) * 5)

        # 知识质量：基于用户满意度和完整性
        knowledge_quality = min(5.0, web_metrics.user_satisfaction_rating *
                               web_metrics.coverage_completeness)

        return {
            "multi_step_reasoning_score": reasoning_score,
            "domain_expertise_score": domain_expertise,
            "synthesis_capability_score": synthesis_capability,
            "independence_score": independence,
            "knowledge_extraction_score": knowledge_extraction,
            "knowledge_organization_score": knowledge_organization,
            "knowledge_reuse_potential": knowledge_reuse,
            "knowledge_quality_score": knowledge_quality,
            "created_knowledge_units": web_metrics.sources_used + web_metrics.citation_count
        }

    def validate_interaction_data(self, task_data: Dict[str, Any]) -> bool:
        """
        验证Web交互数据的完整性

        Args:
            task_data: 任务数据

        Returns:
            bool: 数据是否有效
        """
        required_fields = ["id", "prompt", "article"]

        for field in required_fields:
            if field not in task_data:
                logger.error(f"缺少必需字段: {field}")
                return False

        if "interaction_metrics" in task_data:
            interaction_metrics = task_data["interaction_metrics"]

            # 检查关键的交互指标
            if "timing" not in interaction_metrics:
                logger.warning("缺少timing数据")
                return False

            if "token_usage" not in interaction_metrics:
                logger.warning("缺少token_usage数据")
                return False

            if "performance_metrics" not in interaction_metrics:
                logger.warning("缺少performance_metrics数据")
                return False

        return True

    def get_metrics_summary(self, web_metrics: WebInteractionMetrics) -> Dict[str, Any]:
        """
        获取Web交互指标摘要

        Args:
            web_metrics: Web交互指标

        Returns:
            Dict[str, Any]: 指标摘要
        """
        return {
            "basic_info": {
                "task_id": web_metrics.task_id,
                "model_name": web_metrics.model_name,
                "duration_minutes": round(web_metrics.total_duration_seconds / 60, 2),
                "total_tokens": web_metrics.total_input_tokens + web_metrics.total_output_tokens
            },
            "efficiency": {
                "time_savings_hours": round(web_metrics.time_savings_hours, 2),
                "cost_saving_usd": round(web_metrics.cost_saving_usd, 2),
                "automation_rate": round(web_metrics.automation_rate, 3),
                "efficiency_vs_expert": round(web_metrics.efficiency_vs_expert, 3)
            },
            "quality": {
                "word_count": web_metrics.word_count,
                "sources_used": web_metrics.sources_used,
                "citation_count": web_metrics.citation_count,
                "user_satisfaction": web_metrics.user_satisfaction_rating,
                "coverage_completeness": round(web_metrics.coverage_completeness, 3)
            },
            "performance": {
                "error_rate": round(web_metrics.error_rate, 3),
                "retry_count": web_metrics.retry_count,
                "tool_calls_count": web_metrics.tool_calls_count,
                "successful_tool_rate": round(web_metrics.successful_tool_rate, 3)
            }
        }