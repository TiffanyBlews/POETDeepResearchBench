"""
战略价值评估模块 (Strategic Value Evaluation)
用于评估AI智能体在复杂任务处理和知识沉淀方面的战略价值
"""

import json
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from collections import defaultdict
import hashlib
import pickle
from .api import AIClient

logger = logging.getLogger(__name__)

@dataclass
class StrategicMetrics:
    """战略价值评估指标数据类"""
    task_id: str
    task_title: str
    task_complexity_level: int  # 1-5级复杂度

    # 复杂任务处理能力指标
    multi_step_reasoning_score: float  # 多步推理能力评分
    domain_expertise_score: float     # 领域专业知识评分
    synthesis_capability_score: float  # 信息综合能力评分
    independence_score: float          # 独立完成能力评分

    # 知识沉淀与复用指标
    knowledge_extraction_score: float  # 知识提取能力评分
    knowledge_organization_score: float # 知识组织能力评分
    knowledge_reuse_potential: float   # 知识复用潜力评分
    knowledge_quality_score: float     # 知识质量评分

    # 附加指标
    task_duration_minutes: float
    created_knowledge_units: int       # 创建的知识单元数量
    reused_knowledge_units: int        # 复用的知识单元数量
    knowledge_consistency_score: float # 知识一致性评分

    # 综合评分
    overall_strategic_score: float

@dataclass
class KnowledgeUnit:
    """知识单元数据类"""
    id: str
    content: str
    domain: str
    source_task_id: str
    creation_time: datetime
    usage_count: int = 0
    quality_score: float = 0.0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class KnowledgeBase:
    """知识库管理器"""

    def __init__(self, kb_path: str = "knowledge_base.json"):
        self.kb_path = kb_path
        self.knowledge_units = {}
        self.domain_index = defaultdict(list)
        self.tag_index = defaultdict(list)
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """从文件加载知识库"""
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for unit_data in data.get('knowledge_units', []):
                    unit = KnowledgeUnit(
                        id=unit_data['id'],
                        content=unit_data['content'],
                        domain=unit_data['domain'],
                        source_task_id=unit_data['source_task_id'],
                        creation_time=datetime.fromisoformat(unit_data['creation_time']),
                        usage_count=unit_data.get('usage_count', 0),
                        quality_score=unit_data.get('quality_score', 0.0),
                        tags=unit_data.get('tags', [])
                    )
                    self.add_knowledge_unit(unit, save=False)

                logger.info(f"已加载 {len(self.knowledge_units)} 个知识单元")

            except Exception as e:
                logger.error(f"加载知识库失败: {e}")

    def save_knowledge_base(self):
        """保存知识库到文件"""
        try:
            data = {
                'knowledge_units': [],
                'metadata': {
                    'total_units': len(self.knowledge_units),
                    'last_updated': datetime.now().isoformat()
                }
            }

            for unit in self.knowledge_units.values():
                unit_data = {
                    'id': unit.id,
                    'content': unit.content,
                    'domain': unit.domain,
                    'source_task_id': unit.source_task_id,
                    'creation_time': unit.creation_time.isoformat(),
                    'usage_count': unit.usage_count,
                    'quality_score': unit.quality_score,
                    'tags': unit.tags
                }
                data['knowledge_units'].append(unit_data)

            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存知识库失败: {e}")

    def add_knowledge_unit(self, unit: KnowledgeUnit, save: bool = True):
        """添加知识单元"""
        self.knowledge_units[unit.id] = unit
        self.domain_index[unit.domain].append(unit.id)

        for tag in unit.tags:
            self.tag_index[tag].append(unit.id)

        if save:
            self.save_knowledge_base()

    def find_relevant_knowledge(self, domain: str, tags: List[str] = None, content_keywords: List[str] = None) -> List[KnowledgeUnit]:
        """查找相关知识"""
        relevant_units = []

        # 按领域查找
        candidate_ids = set(self.domain_index.get(domain, []))

        # 按标签过滤
        if tags:
            tag_ids = set()
            for tag in tags:
                tag_ids.update(self.tag_index.get(tag, []))
            candidate_ids = candidate_ids.intersection(tag_ids) if candidate_ids else tag_ids

        # 按内容关键词过滤
        if content_keywords:
            keyword_ids = set()
            for unit_id, unit in self.knowledge_units.items():
                if any(keyword.lower() in unit.content.lower() for keyword in content_keywords):
                    keyword_ids.add(unit_id)
            candidate_ids = candidate_ids.intersection(keyword_ids) if candidate_ids else keyword_ids

        # 收集相关单元
        for unit_id in candidate_ids:
            if unit_id in self.knowledge_units:
                relevant_units.append(self.knowledge_units[unit_id])

        # 按质量分数排序
        relevant_units.sort(key=lambda x: x.quality_score, reverse=True)

        return relevant_units

    def update_knowledge_usage(self, unit_id: str):
        """更新知识使用次数"""
        if unit_id in self.knowledge_units:
            self.knowledge_units[unit_id].usage_count += 1
            self.save_knowledge_base()

class StrategicEvaluator:
    """战略价值评估器"""

    def __init__(self, ai_client: AIClient = None, knowledge_base: KnowledgeBase = None):
        """
        初始化战略价值评估器

        Args:
            ai_client: AI客户端，用于LLM评估
            knowledge_base: 知识库管理器
        """
        self.ai_client = ai_client or AIClient()
        self.knowledge_base = knowledge_base or KnowledgeBase()

    def evaluate_complex_task_capability(self,
                                       task_content: str,
                                       agent_output: str,
                                       reference_output: str = None,
                                       domain: str = "general") -> Dict[str, float]:
        """
        评估复杂任务处理能力

        Args:
            task_content: 任务内容
            agent_output: 智能体输出
            reference_output: 参考输出（可选）
            domain: 任务领域

        Returns:
            Dict[str, float]: 各项能力评分
        """
        evaluation_prompt = f"""
请评估AI智能体在以下复杂任务中的表现，给出1-5分的评分（5分最高）：

任务内容：
{task_content}

AI智能体输出：
{agent_output}

{'参考输出：' + reference_output if reference_output else ''}

请从以下4个维度评估：

1. 多步推理能力 (Multi-step Reasoning)：
   - 能否进行复杂的逻辑推理
   - 推理步骤是否清晰、合理
   - 能否处理多层次的因果关系

2. 领域专业知识 (Domain Expertise)：
   - 是否准确运用专业知识
   - 知识深度是否足够
   - 是否展现对领域的深度理解

3. 信息综合能力 (Synthesis Capability)：
   - 能否有效整合多源信息
   - 信息处理的全面性如何
   - 是否能提炼出核心洞察

4. 独立完成能力 (Independence)：
   - 是否需要人工干预
   - 任务完成的自主性如何
   - 处理不确定性的能力

请以JSON格式输出评分：
{{
    "multi_step_reasoning_score": 评分,
    "domain_expertise_score": 评分,
    "synthesis_capability_score": 评分,
    "independence_score": 评分,
    "overall_reasoning": "综合评价说明"
}}
"""

        try:
            response = self.ai_client.generate(evaluation_prompt)
            # 解析JSON响应
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "multi_step_reasoning_score": float(result.get("multi_step_reasoning_score", 3.0)),
                    "domain_expertise_score": float(result.get("domain_expertise_score", 3.0)),
                    "synthesis_capability_score": float(result.get("synthesis_capability_score", 3.0)),
                    "independence_score": float(result.get("independence_score", 3.0))
                }
        except Exception as e:
            logger.error(f"复杂任务能力评估失败: {e}")

        # 返回默认分数
        return {
            "multi_step_reasoning_score": 3.0,
            "domain_expertise_score": 3.0,
            "synthesis_capability_score": 3.0,
            "independence_score": 3.0
        }

    def evaluate_knowledge_capabilities(self,
                                      task_content: str,
                                      agent_output: str,
                                      extracted_knowledge: List[str],
                                      domain: str = "general") -> Dict[str, float]:
        """
        评估知识沉淀与复用能力

        Args:
            task_content: 任务内容
            agent_output: 智能体输出
            extracted_knowledge: 提取的知识列表
            domain: 任务领域

        Returns:
            Dict[str, float]: 知识相关能力评分
        """
        knowledge_evaluation_prompt = f"""
请评估AI智能体在知识处理方面的能力，给出1-5分的评分（5分最高）：

任务内容：
{task_content}

AI智能体输出：
{agent_output}

提取的知识内容：
{chr(10).join(f"{i+1}. {k}" for i, k in enumerate(extracted_knowledge[:10]))}

请从以下4个维度评估：

1. 知识提取能力 (Knowledge Extraction)：
   - 能否从复杂信息中提取关键知识
   - 提取的知识是否准确、有价值
   - 知识颗粒度是否合适

2. 知识组织能力 (Knowledge Organization)：
   - 知识结构是否清晰、有逻辑
   - 是否能建立知识间的关联
   - 分类和标记是否合理

3. 知识复用潜力 (Knowledge Reuse Potential)：
   - 提取的知识是否具有通用性
   - 能否在其他任务中应用
   - 知识的可迁移性如何

4. 知识质量 (Knowledge Quality)：
   - 知识的准确性如何
   - 信息的完整性和深度
   - 是否包含有价值的洞察

请以JSON格式输出评分：
{{
    "knowledge_extraction_score": 评分,
    "knowledge_organization_score": 评分,
    "knowledge_reuse_potential": 评分,
    "knowledge_quality_score": 评分,
    "knowledge_reasoning": "评价说明"
}}
"""

        try:
            response = self.ai_client.generate(knowledge_evaluation_prompt)
            # 解析JSON响应
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "knowledge_extraction_score": float(result.get("knowledge_extraction_score", 3.0)),
                    "knowledge_organization_score": float(result.get("knowledge_organization_score", 3.0)),
                    "knowledge_reuse_potential": float(result.get("knowledge_reuse_potential", 3.0)),
                    "knowledge_quality_score": float(result.get("knowledge_quality_score", 3.0))
                }
        except Exception as e:
            logger.error(f"知识能力评估失败: {e}")

        # 返回默认分数
        return {
            "knowledge_extraction_score": 3.0,
            "knowledge_organization_score": 3.0,
            "knowledge_reuse_potential": 3.0,
            "knowledge_quality_score": 3.0
        }

    def extract_knowledge_units(self,
                              task_content: str,
                              agent_output: str,
                              task_id: str,
                              domain: str = "general") -> List[KnowledgeUnit]:
        """
        从任务输出中提取知识单元

        Args:
            task_content: 任务内容
            agent_output: 智能体输出
            task_id: 任务ID
            domain: 任务领域

        Returns:
            List[KnowledgeUnit]: 提取的知识单元列表
        """
        knowledge_extraction_prompt = f"""
请从以下AI智能体的输出中提取可复用的知识单元。每个知识单元应该是独立的、有价值的信息片段，可以在其他相关任务中复用。

任务内容：
{task_content}

AI智能体输出：
{agent_output}

请提取知识单元，每个知识单元包括：
1. 具体的知识内容
2. 适用的标签（如：市场分析、技术趋势、行业数据等）
3. 知识类型（如：事实、方法、观点、数据等）

请以JSON格式输出：
{{
    "knowledge_units": [
        {{
            "content": "具体的知识内容",
            "tags": ["标签1", "标签2"],
            "type": "知识类型"
        }}
    ]
}}
"""

        knowledge_units = []

        try:
            response = self.ai_client.generate(knowledge_extraction_prompt)
            # 解析JSON响应
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                for i, unit_data in enumerate(result.get("knowledge_units", [])):
                    # 生成唯一ID
                    content_hash = hashlib.md5(unit_data["content"].encode()).hexdigest()[:8]
                    unit_id = f"{task_id}_{i}_{content_hash}"

                    unit = KnowledgeUnit(
                        id=unit_id,
                        content=unit_data["content"],
                        domain=domain,
                        source_task_id=task_id,
                        creation_time=datetime.now(),
                        tags=unit_data.get("tags", [])
                    )

                    knowledge_units.append(unit)

        except Exception as e:
            logger.error(f"知识提取失败: {e}")

        return knowledge_units

    def calculate_knowledge_consistency(self, new_units: List[KnowledgeUnit], domain: str) -> float:
        """
        计算新知识与已有知识的一致性

        Args:
            new_units: 新的知识单元
            domain: 领域

        Returns:
            float: 一致性评分 (0-1)
        """
        if not new_units:
            return 1.0

        existing_units = self.knowledge_base.find_relevant_knowledge(domain)

        if not existing_units:
            return 1.0  # 没有现有知识，认为一致

        # 简单的一致性检查（可以改进为更复杂的语义相似度计算）
        consistency_scores = []

        for new_unit in new_units:
            max_similarity = 0.0

            for existing_unit in existing_units[:10]:  # 只检查前10个最相关的
                # 简单的文本相似度计算
                new_words = set(new_unit.content.lower().split())
                existing_words = set(existing_unit.content.lower().split())

                if new_words and existing_words:
                    intersection = len(new_words & existing_words)
                    union = len(new_words | existing_words)
                    similarity = intersection / union if union > 0 else 0

                    max_similarity = max(max_similarity, similarity)

            consistency_scores.append(max_similarity)

        return sum(consistency_scores) / len(consistency_scores)

    def evaluate_strategic_value(self,
                               task_id: str,
                               task_title: str,
                               task_content: str,
                               agent_output: str,
                               task_duration_minutes: float,
                               domain: str = "general",
                               complexity_level: int = 3,
                               reference_output: str = None) -> StrategicMetrics:
        """
        综合评估战略价值

        Args:
            task_id: 任务ID
            task_title: 任务标题
            task_content: 任务内容
            agent_output: 智能体输出
            task_duration_minutes: 任务持续时间（分钟）
            domain: 任务领域
            complexity_level: 复杂度级别 (1-5)
            reference_output: 参考输出

        Returns:
            StrategicMetrics: 战略价值评估结果
        """
        logger.info(f"开始战略价值评估: {task_id}")

        # 1. 评估复杂任务处理能力
        complex_task_scores = self.evaluate_complex_task_capability(
            task_content, agent_output, reference_output, domain
        )

        # 2. 提取知识单元
        knowledge_units = self.extract_knowledge_units(
            task_content, agent_output, task_id, domain
        )

        # 3. 评估知识相关能力
        knowledge_scores = self.evaluate_knowledge_capabilities(
            task_content, agent_output, [unit.content for unit in knowledge_units], domain
        )

        # 4. 计算知识一致性
        knowledge_consistency = self.calculate_knowledge_consistency(knowledge_units, domain)

        # 5. 查找复用的知识
        relevant_existing = self.knowledge_base.find_relevant_knowledge(domain)
        reused_count = min(len(relevant_existing), 5)  # 假设最多复用5个现有知识单元

        # 更新知识库
        for unit in knowledge_units:
            self.knowledge_base.add_knowledge_unit(unit)

        # 6. 计算综合战略评分
        overall_score = (
            complex_task_scores["multi_step_reasoning_score"] * 0.25 +
            complex_task_scores["domain_expertise_score"] * 0.20 +
            complex_task_scores["synthesis_capability_score"] * 0.20 +
            complex_task_scores["independence_score"] * 0.15 +
            knowledge_scores["knowledge_extraction_score"] * 0.10 +
            knowledge_scores["knowledge_organization_score"] * 0.05 +
            knowledge_scores["knowledge_reuse_potential"] * 0.05
        )

        # 创建评估结果
        metrics = StrategicMetrics(
            task_id=task_id,
            task_title=task_title,
            task_complexity_level=complexity_level,
            multi_step_reasoning_score=complex_task_scores["multi_step_reasoning_score"],
            domain_expertise_score=complex_task_scores["domain_expertise_score"],
            synthesis_capability_score=complex_task_scores["synthesis_capability_score"],
            independence_score=complex_task_scores["independence_score"],
            knowledge_extraction_score=knowledge_scores["knowledge_extraction_score"],
            knowledge_organization_score=knowledge_scores["knowledge_organization_score"],
            knowledge_reuse_potential=knowledge_scores["knowledge_reuse_potential"],
            knowledge_quality_score=knowledge_scores["knowledge_quality_score"],
            task_duration_minutes=task_duration_minutes,
            created_knowledge_units=len(knowledge_units),
            reused_knowledge_units=reused_count,
            knowledge_consistency_score=knowledge_consistency,
            overall_strategic_score=overall_score
        )

        logger.info(f"战略价值评估完成: 总分 {overall_score:.2f}")

        return metrics

class StrategicBenchmark:
    """战略价值基准测试器"""

    def __init__(self, ai_client: AIClient = None, knowledge_base_path: str = "strategic_kb.json"):
        """
        初始化战略基准测试器

        Args:
            ai_client: AI客户端
            knowledge_base_path: 知识库路径
        """
        self.ai_client = ai_client or AIClient()
        self.knowledge_base = KnowledgeBase(knowledge_base_path)
        self.evaluator = StrategicEvaluator(self.ai_client, self.knowledge_base)
        self.results = []

    def evaluate_batch(self,
                      tasks: List[Dict[str, Any]],
                      output_file: str = None) -> List[StrategicMetrics]:
        """
        批量评估战略价值

        Args:
            tasks: 任务列表
            output_file: 结果输出文件

        Returns:
            List[StrategicMetrics]: 评估结果列表
        """
        results = []

        for i, task in enumerate(tasks, 1):
            logger.info(f"评估任务 {i}/{len(tasks)}: {task.get('task_id', 'unknown')}")

            try:
                start_time = time.time()

                metrics = self.evaluator.evaluate_strategic_value(
                    task_id=task["task_id"],
                    task_title=task.get("task_title", ""),
                    task_content=task["task_content"],
                    agent_output=task["agent_output"],
                    task_duration_minutes=task.get("task_duration_minutes", 60.0),
                    domain=task.get("domain", "general"),
                    complexity_level=task.get("complexity_level", 3),
                    reference_output=task.get("reference_output")
                )

                results.append(metrics)

            except Exception as e:
                logger.error(f"任务 {task.get('task_id')} 战略评估失败: {e}")

        if output_file:
            self.save_results(results, output_file)

        return results

    def save_results(self, results: List[StrategicMetrics], output_file: str):
        """保存评估结果"""
        try:
            results_dict = [asdict(result) for result in results]

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"战略价值评估结果已保存到: {output_file}")

        except Exception as e:
            logger.error(f"保存结果失败: {e}")

    def generate_strategic_report(self, results: List[StrategicMetrics]) -> Dict[str, Any]:
        """生成战略价值评估报告"""
        if not results:
            return {"error": "没有可用的评估结果"}

        report = {
            "summary": {
                "total_tasks": len(results),
                "avg_overall_score": sum(r.overall_strategic_score for r in results) / len(results),
                "avg_complexity_level": sum(r.task_complexity_level for r in results) / len(results)
            },
            "capability_scores": {},
            "knowledge_metrics": {},
            "task_analysis": {}
        }

        # 能力评分分析
        report["capability_scores"] = {
            "avg_multi_step_reasoning": sum(r.multi_step_reasoning_score for r in results) / len(results),
            "avg_domain_expertise": sum(r.domain_expertise_score for r in results) / len(results),
            "avg_synthesis_capability": sum(r.synthesis_capability_score for r in results) / len(results),
            "avg_independence": sum(r.independence_score for r in results) / len(results)
        }

        # 知识指标分析
        report["knowledge_metrics"] = {
            "avg_knowledge_extraction": sum(r.knowledge_extraction_score for r in results) / len(results),
            "avg_knowledge_organization": sum(r.knowledge_organization_score for r in results) / len(results),
            "avg_knowledge_reuse_potential": sum(r.knowledge_reuse_potential for r in results) / len(results),
            "avg_knowledge_quality": sum(r.knowledge_quality_score for r in results) / len(results),
            "total_knowledge_units_created": sum(r.created_knowledge_units for r in results),
            "total_knowledge_units_reused": sum(r.reused_knowledge_units for r in results),
            "avg_knowledge_consistency": sum(r.knowledge_consistency_score for r in results) / len(results)
        }

        # 任务分析
        complexity_groups = defaultdict(list)
        for result in results:
            complexity_groups[result.task_complexity_level].append(result.overall_strategic_score)

        report["task_analysis"] = {
            "performance_by_complexity": {
                level: {
                    "avg_score": sum(scores) / len(scores),
                    "task_count": len(scores)
                }
                for level, scores in complexity_groups.items()
            }
        }

        return report

if __name__ == "__main__":
    # 示例用法
    benchmark = StrategicBenchmark()

    # 模拟任务数据
    sample_tasks = [
        {
            "task_id": "strategic_001",
            "task_title": "市场竞争分析",
            "task_content": "分析电动汽车市场的竞争格局和未来趋势",
            "agent_output": "基于分析，电动汽车市场呈现出特斯拉主导、传统车企转型、新兴品牌涌现的三足鼎立格局...",
            "domain": "market_analysis",
            "complexity_level": 4,
            "task_duration_minutes": 120.0
        }
    ]

    results = benchmark.evaluate_batch(sample_tasks, "strategic_results.json")

    report = benchmark.generate_strategic_report(results)
    print(f"战略价值评估完成，总体评分: {report['summary']['avg_overall_score']:.2f}")