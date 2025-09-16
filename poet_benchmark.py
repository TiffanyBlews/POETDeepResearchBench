"""
POET综合评估脚本 (POET Comprehensive Benchmark)
整合效率价值、质量价值(RACE+FACT)、战略价值三大评估维度
"""

import argparse
import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 导入各个评估模块
from utils.efficiency_evaluator import EfficiencyEvaluator, EfficiencyMetrics
from utils.strategic_evaluator import StrategicEvaluator, StrategicMetrics, KnowledgeBase
from utils.api import AIClient
from utils.io_utils import load_jsonl, save_jsonl

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('poet_benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class POETMetrics:
    """POET综合评估指标"""
    task_id: str
    task_title: str
    model_name: str

    # 基础信息
    query_content: str
    agent_output: str
    domain: str
    complexity_level: int

    # 效率价值 (Efficiency Value)
    efficiency_metrics: EfficiencyMetrics

    # 质量价值 (Quality Value) - RACE + FACT分数
    race_score: float
    fact_citation_accuracy: float
    fact_effective_citations: int

    # 战略价值 (Strategic Value)
    strategic_metrics: StrategicMetrics

    # 综合评分
    overall_poet_score: float
    poet_value_breakdown: Dict[str, float]

    # 评估元数据
    evaluation_timestamp: str
    evaluation_duration_seconds: float

class POETBenchmark:
    """POET综合基准测试器"""

    def __init__(self, config_path: str = None):
        """
        初始化POET基准测试器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.ai_client = AIClient()

        # 初始化各个评估器
        self.efficiency_evaluator = EfficiencyEvaluator(
            expert_time_hours=self.config.get("default_expert_time", 2.0),
            expert_hourly_rate_usd=self.config.get("default_expert_rate", 100.0)
        )

        self.knowledge_base = KnowledgeBase(
            kb_path=self.config.get("knowledge_base_path", "poet_knowledge_base.json")
        )

        self.strategic_evaluator = StrategicEvaluator(
            ai_client=self.ai_client,
            knowledge_base=self.knowledge_base
        )

        self.results = []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "poet_weights": {
                "efficiency_value": 0.30,    # 效率价值权重 30%
                "quality_value": 0.50,       # 质量价值权重 50%
                "strategic_value": 0.20      # 战略价值权重 20%
            },
            "quality_value_weights": {
                "race_score": 0.70,          # RACE分数权重 70%
                "fact_score": 0.30           # FACT分数权重 30%
            },
            "efficiency_weights": {
                "time_weight": 0.40,         # 时间效率权重
                "cost_weight": 0.30,         # 成本效率权重
                "automation_weight": 0.30    # 自动化率权重
            },
            "strategic_weights": {
                "task_capability": 0.60,     # 复杂任务处理能力权重
                "knowledge_capability": 0.40  # 知识能力权重
            },
            "task_complexity_mapping": {
                "simple": 1,
                "moderate": 2,
                "complex": 3,
                "advanced": 4,
                "expert": 5
            },
            "domain_expert_rates": {
                "finance": 150.0,
                "legal": 200.0,
                "medical": 180.0,
                "technology": 120.0,
                "marketing": 100.0,
                "general": 100.0
            },
            "domain_expert_times": {
                "finance": 3.0,
                "legal": 4.0,
                "medical": 5.0,
                "technology": 2.0,
                "marketing": 2.0,
                "general": 2.0
            },
            "default_expert_time": 2.0,
            "default_expert_rate": 100.0,
            "knowledge_base_path": "poet_knowledge_base.json"
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 递归更新配置
                self._deep_update(default_config, user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件 {config_path}: {e}")

        return default_config

    def _deep_update(self, base_dict: dict, update_dict: dict):
        """递归更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _load_race_results(self, race_results_path: str) -> Dict[str, Dict[str, float]]:
        """加载RACE评估结果"""
        race_results = {}

        if os.path.exists(race_results_path):
            try:
                with open(race_results_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 解析RACE结果文件（假设是文本格式）
                # 这里需要根据实际的RACE结果格式进行调整
                lines = content.strip().split('\n')
                for line in lines:
                    if ':' in line and 'score' in line.lower():
                        # 简单解析，实际情况可能需要更复杂的解析逻辑
                        parts = line.split(':')
                        if len(parts) >= 2:
                            try:
                                score = float(parts[1].strip())
                                # 提取任务ID（需要根据实际格式调整）
                                task_id = parts[0].strip()
                                race_results[task_id] = {"race_score": score}
                            except ValueError:
                                continue

            except Exception as e:
                logger.error(f"加载RACE结果失败: {e}")

        return race_results

    def _load_fact_results(self, fact_results_path: str) -> Dict[str, Dict[str, float]]:
        """加载FACT评估结果"""
        fact_results = {}

        if os.path.exists(fact_results_path):
            try:
                with open(fact_results_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 解析FACT结果
                for item in data:
                    if isinstance(item, dict) and 'task_id' in item:
                        task_id = item['task_id']
                        fact_results[task_id] = {
                            "citation_accuracy": item.get('citation_accuracy', 0.0),
                            "effective_citations": item.get('effective_citations', 0)
                        }

            except Exception as e:
                logger.error(f"加载FACT结果失败: {e}")

        return fact_results

    def calculate_efficiency_score(self, metrics: EfficiencyMetrics) -> float:
        """计算效率价值得分 (0-1)"""
        weights = self.config["efficiency_weights"]

        # 时间效率：基于完成时间vs专家时间
        if metrics.expert_time_hours and metrics.expert_time_hours > 0:
            ai_time_hours = metrics.completion_time_seconds / 3600
            time_efficiency = max(0, 1 - (ai_time_hours / metrics.expert_time_hours))
        else:
            time_efficiency = 0.5  # 默认值

        # 成本效率：基于成本节约
        if metrics.cost_saving_usd and metrics.cost_saving_usd > 0:
            expert_cost = metrics.expert_time_hours * metrics.expert_hourly_rate_usd
            cost_efficiency = min(1.0, metrics.cost_saving_usd / expert_cost)
        else:
            cost_efficiency = 0.0

        # 自动化率
        automation_efficiency = metrics.automation_rate or 0.0

        # 综合效率分数
        efficiency_score = (
            time_efficiency * weights["time_weight"] +
            cost_efficiency * weights["cost_weight"] +
            automation_efficiency * weights["automation_weight"]
        )

        return min(1.0, max(0.0, efficiency_score))

    def calculate_quality_score(self, race_score: float, fact_accuracy: float, fact_citations: int) -> float:
        """计算质量价值得分 (0-1)"""
        weights = self.config["quality_value_weights"]

        # 标准化RACE分数 (假设RACE分数范围是0-5)
        normalized_race = min(1.0, max(0.0, race_score / 5.0))

        # 标准化FACT分数
        normalized_fact = min(1.0, max(0.0, fact_accuracy))

        # 综合质量分数
        quality_score = (
            normalized_race * weights["race_score"] +
            normalized_fact * weights["fact_score"]
        )

        return quality_score

    def calculate_strategic_score(self, metrics: StrategicMetrics) -> float:
        """计算战略价值得分 (0-1)"""
        weights = self.config["strategic_weights"]

        # 复杂任务处理能力 (0-5分标准化到0-1)
        task_capability = (
            metrics.multi_step_reasoning_score +
            metrics.domain_expertise_score +
            metrics.synthesis_capability_score +
            metrics.independence_score
        ) / 20.0  # 4个指标，每个最高5分

        # 知识能力 (0-5分标准化到0-1)
        knowledge_capability = (
            metrics.knowledge_extraction_score +
            metrics.knowledge_organization_score +
            metrics.knowledge_reuse_potential +
            metrics.knowledge_quality_score
        ) / 20.0  # 4个指标，每个最高5分

        # 综合战略分数
        strategic_score = (
            task_capability * weights["task_capability"] +
            knowledge_capability * weights["knowledge_capability"]
        )

        return min(1.0, max(0.0, strategic_score))

    def calculate_poet_score(self,
                           efficiency_score: float,
                           quality_score: float,
                           strategic_score: float) -> Tuple[float, Dict[str, float]]:
        """计算POET综合得分"""
        weights = self.config["poet_weights"]

        poet_score = (
            efficiency_score * weights["efficiency_value"] +
            quality_score * weights["quality_value"] +
            strategic_score * weights["strategic_value"]
        )

        breakdown = {
            "efficiency_value": efficiency_score,
            "quality_value": quality_score,
            "strategic_value": strategic_score
        }

        return poet_score, breakdown

    def evaluate_single_task(self,
                           task_data: Dict[str, Any],
                           race_results: Dict[str, Dict[str, float]] = None,
                           fact_results: Dict[str, Dict[str, float]] = None) -> POETMetrics:
        """评估单个任务"""
        task_id = task_data["id"]
        logger.info(f"开始POET评估: {task_id}")

        start_time = time.time()

        # 提取任务信息
        task_content = task_data.get("prompt", "")
        agent_output = task_data.get("article", "")
        domain = task_data.get("domain", "general")
        model_name = task_data.get("model_name", "unknown")

        # 确定复杂度级别
        complexity_level = task_data.get("complexity_level", 3)
        if isinstance(complexity_level, str):
            complexity_level = self.config["task_complexity_mapping"].get(complexity_level, 3)

        # 获取领域特定的专家参数
        expert_time = self.config["domain_expert_times"].get(domain, self.config["default_expert_time"])
        expert_rate = self.config["domain_expert_rates"].get(domain, self.config["default_expert_rate"])

        # 1. 效率价值评估
        self.efficiency_evaluator.expert_time_hours = expert_time
        self.efficiency_evaluator.expert_hourly_rate_usd = expert_rate

        self.efficiency_evaluator.start_task(task_id, task_content)

        # 模拟token使用（实际使用中应该从真实的模型调用中获取）
        estimated_input_tokens = len(task_content.split()) * 1.3  # 粗略估算
        estimated_output_tokens = len(agent_output.split()) * 1.3
        self.efficiency_evaluator.add_token_usage(
            int(estimated_input_tokens),
            int(estimated_output_tokens)
        )

        efficiency_metrics = self.efficiency_evaluator.end_task(success=True)

        # 2. 战略价值评估
        strategic_metrics = self.strategic_evaluator.evaluate_strategic_value(
            task_id=task_id,
            task_title=task_data.get("title", ""),
            task_content=task_content,
            agent_output=agent_output,
            task_duration_minutes=efficiency_metrics.completion_time_seconds / 60,
            domain=domain,
            complexity_level=complexity_level
        )

        # 3. 获取质量价值数据 (RACE + FACT)
        race_score = 0.0
        fact_accuracy = 0.0
        fact_citations = 0

        if race_results and task_id in race_results:
            race_score = race_results[task_id].get("race_score", 0.0)

        if fact_results and task_id in fact_results:
            fact_data = fact_results[task_id]
            fact_accuracy = fact_data.get("citation_accuracy", 0.0)
            fact_citations = fact_data.get("effective_citations", 0)

        # 4. 计算各维度得分
        efficiency_score = self.calculate_efficiency_score(efficiency_metrics)
        quality_score = self.calculate_quality_score(race_score, fact_accuracy, fact_citations)
        strategic_score = self.calculate_strategic_score(strategic_metrics)

        # 5. 计算POET综合得分
        poet_score, value_breakdown = self.calculate_poet_score(
            efficiency_score, quality_score, strategic_score
        )

        evaluation_duration = time.time() - start_time

        # 创建POET评估结果
        poet_metrics = POETMetrics(
            task_id=task_id,
            task_title=task_data.get("title", ""),
            model_name=model_name,
            query_content=task_content,
            agent_output=agent_output,
            domain=domain,
            complexity_level=complexity_level,
            efficiency_metrics=efficiency_metrics,
            race_score=race_score,
            fact_citation_accuracy=fact_accuracy,
            fact_effective_citations=fact_citations,
            strategic_metrics=strategic_metrics,
            overall_poet_score=poet_score,
            poet_value_breakdown=value_breakdown,
            evaluation_timestamp=datetime.now().isoformat(),
            evaluation_duration_seconds=evaluation_duration
        )

        logger.info(f"POET评估完成 {task_id}: 总分 {poet_score:.3f}")

        return poet_metrics

    def evaluate_batch(self,
                      input_file: str,
                      output_dir: str,
                      model_name: str,
                      race_results_path: str = None,
                      fact_results_path: str = None,
                      max_workers: int = 4,
                      limit: int = None) -> List[POETMetrics]:
        """批量评估"""
        logger.info(f"开始POET批量评估: {model_name}")

        # 加载输入数据
        tasks = load_jsonl(input_file)
        if limit:
            tasks = tasks[:limit]

        # 加载RACE和FACT结果
        race_results = self._load_race_results(race_results_path) if race_results_path else {}
        fact_results = self._load_fact_results(fact_results_path) if fact_results_path else {}

        logger.info(f"加载 {len(tasks)} 个任务进行评估")

        results = []
        start_time = time.time()

        # 并发评估
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(
                    self.evaluate_single_task,
                    {**task, "model_name": model_name},
                    race_results,
                    fact_results
                ): task
                for task in tasks
            }

            completed = 0
            for future in as_completed(future_to_task):
                completed += 1
                try:
                    result = future.result()
                    results.append(result)

                    if completed % 10 == 0:
                        logger.info(f"评估进度: {completed}/{len(tasks)}")

                except Exception as e:
                    task = future_to_task[future]
                    logger.error(f"任务 {task.get('id', 'unknown')} 评估失败: {e}")

        total_time = time.time() - start_time
        logger.info(f"批量评估完成，耗时 {total_time:.2f}秒")

        # 保存结果
        self.save_results(results, output_dir, model_name)

        # 生成报告
        self.generate_poet_report(results, output_dir, model_name)

        return results

    def save_results(self, results: List[POETMetrics], output_dir: str, model_name: str):
        """保存评估结果"""
        os.makedirs(output_dir, exist_ok=True)

        # 保存详细结果
        detailed_results = []
        for result in results:
            result_dict = asdict(result)
            # 处理datetime序列化
            if 'evaluation_timestamp' in result_dict:
                result_dict['evaluation_timestamp'] = str(result_dict['evaluation_timestamp'])
            detailed_results.append(result_dict)

        detailed_file = os.path.join(output_dir, f"{model_name}_poet_detailed.json")
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2, default=str)

        # 保存汇总结果
        summary_results = []
        for result in results:
            summary = {
                "task_id": result.task_id,
                "model_name": result.model_name,
                "domain": result.domain,
                "complexity_level": result.complexity_level,
                "overall_poet_score": result.overall_poet_score,
                "efficiency_score": result.poet_value_breakdown["efficiency_value"],
                "quality_score": result.poet_value_breakdown["quality_value"],
                "strategic_score": result.poet_value_breakdown["strategic_value"],
                "race_score": result.race_score,
                "fact_accuracy": result.fact_citation_accuracy,
                "cost_saving_usd": result.efficiency_metrics.cost_saving_usd,
                "automation_rate": result.efficiency_metrics.automation_rate,
                "knowledge_units_created": result.strategic_metrics.created_knowledge_units
            }
            summary_results.append(summary)

        summary_file = os.path.join(output_dir, f"{model_name}_poet_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_results, f, ensure_ascii=False, indent=2)

        logger.info(f"POET评估结果已保存到 {output_dir}")

    def generate_poet_report(self, results: List[POETMetrics], output_dir: str, model_name: str):
        """生成POET评估报告"""
        if not results:
            logger.warning("没有评估结果，无法生成报告")
            return

        report = {
            "model_name": model_name,
            "evaluation_summary": {
                "total_tasks": len(results),
                "evaluation_time": datetime.now().isoformat(),
                "avg_poet_score": sum(r.overall_poet_score for r in results) / len(results)
            },
            "poet_value_analysis": {
                "efficiency_value": {
                    "avg_score": sum(r.poet_value_breakdown["efficiency_value"] for r in results) / len(results),
                    "avg_time_savings_hours": sum((r.efficiency_metrics.expert_time_hours or 0) - (r.efficiency_metrics.completion_time_seconds / 3600) for r in results) / len(results),
                    "total_cost_savings_usd": sum(r.efficiency_metrics.cost_saving_usd or 0 for r in results),
                    "avg_automation_rate": sum(r.efficiency_metrics.automation_rate or 0 for r in results) / len(results)
                },
                "quality_value": {
                    "avg_score": sum(r.poet_value_breakdown["quality_value"] for r in results) / len(results),
                    "avg_race_score": sum(r.race_score for r in results) / len(results),
                    "avg_fact_accuracy": sum(r.fact_citation_accuracy for r in results) / len(results),
                    "total_effective_citations": sum(r.fact_effective_citations for r in results)
                },
                "strategic_value": {
                    "avg_score": sum(r.poet_value_breakdown["strategic_value"] for r in results) / len(results),
                    "avg_reasoning_score": sum(r.strategic_metrics.multi_step_reasoning_score for r in results) / len(results),
                    "avg_domain_expertise": sum(r.strategic_metrics.domain_expertise_score for r in results) / len(results),
                    "total_knowledge_units": sum(r.strategic_metrics.created_knowledge_units for r in results),
                    "avg_knowledge_quality": sum(r.strategic_metrics.knowledge_quality_score for r in results) / len(results)
                }
            },
            "domain_analysis": {},
            "complexity_analysis": {},
            "top_performing_tasks": [],
            "improvement_recommendations": []
        }

        # 领域分析
        from collections import defaultdict
        domain_stats = defaultdict(list)
        complexity_stats = defaultdict(list)

        for result in results:
            domain_stats[result.domain].append(result.overall_poet_score)
            complexity_stats[result.complexity_level].append(result.overall_poet_score)

        report["domain_analysis"] = {
            domain: {
                "task_count": len(scores),
                "avg_poet_score": sum(scores) / len(scores),
                "max_poet_score": max(scores),
                "min_poet_score": min(scores)
            }
            for domain, scores in domain_stats.items()
        }

        report["complexity_analysis"] = {
            f"level_{level}": {
                "task_count": len(scores),
                "avg_poet_score": sum(scores) / len(scores)
            }
            for level, scores in complexity_stats.items()
        }

        # 前10名任务
        top_tasks = sorted(results, key=lambda x: x.overall_poet_score, reverse=True)[:10]
        report["top_performing_tasks"] = [
            {
                "task_id": task.task_id,
                "poet_score": task.overall_poet_score,
                "domain": task.domain,
                "complexity": task.complexity_level
            }
            for task in top_tasks
        ]

        # 改进建议
        avg_efficiency = sum(r.poet_value_breakdown["efficiency_value"] for r in results) / len(results)
        avg_quality = sum(r.poet_value_breakdown["quality_value"] for r in results) / len(results)
        avg_strategic = sum(r.poet_value_breakdown["strategic_value"] for r in results) / len(results)

        recommendations = []
        if avg_efficiency < 0.6:
            recommendations.append("建议优化效率：减少任务完成时间，提高自动化程度")
        if avg_quality < 0.6:
            recommendations.append("建议提升质量：改进信息准确性和引用质量")
        if avg_strategic < 0.6:
            recommendations.append("建议增强战略能力：提升复杂推理和知识沉淀能力")

        report["improvement_recommendations"] = recommendations

        # 保存报告
        report_file = os.path.join(output_dir, f"{model_name}_poet_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成文本报告
        self._generate_text_report(report, output_dir, model_name)

        logger.info(f"POET评估报告已生成: {report_file}")

    def _generate_text_report(self, report: Dict[str, Any], output_dir: str, model_name: str):
        """生成文本格式的报告"""
        text_report = f"""
# POET 综合评估报告

## 模型信息
- 模型名称: {report['model_name']}
- 评估时间: {report['evaluation_summary']['evaluation_time']}
- 评估任务数: {report['evaluation_summary']['total_tasks']}

## 综合表现
- **POET总分**: {report['evaluation_summary']['avg_poet_score']:.3f}

## 三大价值维度分析

### 1. 效率价值 (Efficiency Value)
- 效率得分: {report['poet_value_analysis']['efficiency_value']['avg_score']:.3f}
- 平均时间节约: {report['poet_value_analysis']['efficiency_value']['avg_time_savings_hours']:.2f} 小时
- 总成本节约: ${report['poet_value_analysis']['efficiency_value']['total_cost_savings_usd']:.2f}
- 平均自动化率: {report['poet_value_analysis']['efficiency_value']['avg_automation_rate']:.1%}

### 2. 质量价值 (Quality Value)
- 质量得分: {report['poet_value_analysis']['quality_value']['avg_score']:.3f}
- 平均RACE分数: {report['poet_value_analysis']['quality_value']['avg_race_score']:.2f}
- 平均引用准确率: {report['poet_value_analysis']['quality_value']['avg_fact_accuracy']:.1%}
- 有效引用总数: {report['poet_value_analysis']['quality_value']['total_effective_citations']}

### 3. 战略价值 (Strategic Value)
- 战略得分: {report['poet_value_analysis']['strategic_value']['avg_score']:.3f}
- 平均推理能力: {report['poet_value_analysis']['strategic_value']['avg_reasoning_score']:.2f}/5
- 平均领域专业度: {report['poet_value_analysis']['strategic_value']['avg_domain_expertise']:.2f}/5
- 知识单元创建总数: {report['poet_value_analysis']['strategic_value']['total_knowledge_units']}
- 平均知识质量: {report['poet_value_analysis']['strategic_value']['avg_knowledge_quality']:.2f}/5

## 领域表现分析
"""

        for domain, stats in report['domain_analysis'].items():
            text_report += f"""
### {domain} 领域
- 任务数量: {stats['task_count']}
- 平均得分: {stats['avg_poet_score']:.3f}
- 最高得分: {stats['max_poet_score']:.3f}
- 最低得分: {stats['min_poet_score']:.3f}
"""

        text_report += "\n## 复杂度表现分析\n"
        for level, stats in report['complexity_analysis'].items():
            text_report += f"""
### 复杂度 {level}
- 任务数量: {stats['task_count']}
- 平均得分: {stats['avg_poet_score']:.3f}
"""

        text_report += "\n## 改进建议\n"
        for i, rec in enumerate(report['improvement_recommendations'], 1):
            text_report += f"{i}. {rec}\n"

        # 保存文本报告
        text_file = os.path.join(output_dir, f"{model_name}_poet_report.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)

def main():
    parser = argparse.ArgumentParser(description='POET综合基准评估')
    parser.add_argument('model_name', help='模型名称')
    parser.add_argument('--input_file', required=True, help='输入文件路径 (JSONL格式)')
    parser.add_argument('--output_dir', required=True, help='输出目录')
    parser.add_argument('--race_results', help='RACE评估结果文件路径')
    parser.add_argument('--fact_results', help='FACT评估结果文件路径')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--max_workers', type=int, default=4, help='最大并发数')
    parser.add_argument('--limit', type=int, help='限制评估任务数量')

    args = parser.parse_args()

    # 创建POET基准测试器
    benchmark = POETBenchmark(config_path=args.config)

    # 执行评估
    results = benchmark.evaluate_batch(
        input_file=args.input_file,
        output_dir=args.output_dir,
        model_name=args.model_name,
        race_results_path=args.race_results,
        fact_results_path=args.fact_results,
        max_workers=args.max_workers,
        limit=args.limit
    )

    logger.info(f"POET评估完成！共评估 {len(results)} 个任务")

    if results:
        avg_score = sum(r.overall_poet_score for r in results) / len(results)
        logger.info(f"模型 {args.model_name} 的平均POET得分: {avg_score:.3f}")

if __name__ == "__main__":
    main()