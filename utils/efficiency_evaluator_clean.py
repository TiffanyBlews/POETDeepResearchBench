"""
效率价值评估模块 (Efficiency Value Evaluation)
用于评估AI智能体在任务执行中的效率表现
重构版本：移除硬编码数据，使用外部标注文件
"""

import time
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from .api import AIClient
from .enhanced_annotation_loader import EnhancedAnnotationLoader

logger = logging.getLogger(__name__)

@dataclass
class EfficiencyMetrics:
    """效率评估指标数据类"""
    task_id: str
    task_title: str

    # 时间相关指标
    start_time: float
    end_time: float
    completion_time_seconds: float

    # Token相关指标
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # 成本相关指标
    estimated_cost_usd: float

    # 人力对比指标
    expert_time_hours: Optional[float] = None
    expert_hourly_rate_usd: Optional[float] = None
    automation_rate: Optional[float] = None
    cost_saving_usd: Optional[float] = None

    # 质量指标
    task_success: bool = True
    error_count: int = 0

class EfficiencyEvaluator:
    """效率价值评估器"""

    def __init__(self,
                 expert_time_hours: float = 1.0,
                 expert_hourly_rate_usd: float = 100.0,
                 token_cost_per_1k_input: float = 0.0015,
                 token_cost_per_1k_output: float = 0.006):
        """
        初始化效率评估器

        Args:
            expert_time_hours: 专家完成同等任务的时间（小时）
            expert_hourly_rate_usd: 专家时薪（美元）
            token_cost_per_1k_input: 每1000个输入token的成本
            token_cost_per_1k_output: 每1000个输出token的成本
        """
        self.expert_time_hours = expert_time_hours
        self.expert_hourly_rate_usd = expert_hourly_rate_usd
        self.token_cost_per_1k_input = token_cost_per_1k_input
        self.token_cost_per_1k_output = token_cost_per_1k_output

        # 用于跟踪当前任务
        self.current_task_id = None
        self.start_time = None
        self.token_usage = {"input": 0, "output": 0}
        self.error_count = 0

    def start_task(self, task_id: str, task_title: str = ""):
        """开始一个任务的效率评估"""
        self.current_task_id = task_id
        self.current_task_title = task_title
        self.start_time = time.time()
        self.token_usage = {"input": 0, "output": 0}
        self.error_count = 0

        logger.info(f"开始效率评估: {task_id} - {task_title}")

    def add_token_usage(self, input_tokens: int, output_tokens: int):
        """添加token使用量"""
        self.token_usage["input"] += input_tokens
        self.token_usage["output"] += output_tokens

    def add_error(self):
        """记录错误次数"""
        self.error_count += 1

    def end_task(self, success: bool = True) -> EfficiencyMetrics:
        """结束任务并计算效率指标"""
        if self.current_task_id is None:
            raise ValueError("没有正在进行的任务")

        end_time = time.time()
        completion_time_seconds = end_time - self.start_time

        # 计算成本
        estimated_cost = self._calculate_cost(
            self.token_usage["input"],
            self.token_usage["output"]
        )

        # 计算自动化率和成本节约
        automation_rate = self._calculate_automation_rate(completion_time_seconds)
        cost_saving = self._calculate_cost_saving(completion_time_seconds)

        metrics = EfficiencyMetrics(
            task_id=self.current_task_id,
            task_title=self.current_task_title,
            start_time=self.start_time,
            end_time=end_time,
            completion_time_seconds=completion_time_seconds,
            input_tokens=self.token_usage["input"],
            output_tokens=self.token_usage["output"],
            total_tokens=self.token_usage["input"] + self.token_usage["output"],
            estimated_cost_usd=estimated_cost,
            expert_time_hours=self.expert_time_hours,
            expert_hourly_rate_usd=self.expert_hourly_rate_usd,
            automation_rate=automation_rate,
            cost_saving_usd=cost_saving,
            task_success=success,
            error_count=self.error_count
        )

        # 重置状态
        self.current_task_id = None
        self.start_time = None

        logger.info(f"任务完成 - 耗时: {completion_time_seconds:.2f}秒, 成本: ${estimated_cost:.4f}, 节约: ${cost_saving:.2f}")

        return metrics

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算token成本"""
        input_cost = (input_tokens / 1000) * self.token_cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.token_cost_per_1k_output
        return input_cost + output_cost

    def _calculate_automation_rate(self, completion_time_seconds: float) -> float:
        """计算自动化率"""
        ai_time_hours = completion_time_seconds / 3600
        if self.expert_time_hours <= 0:
            return 1.0
        automation_rate = 1 - (ai_time_hours / self.expert_time_hours)
        return max(0.0, min(1.0, automation_rate))  # 限制在0-1之间

    def _calculate_cost_saving(self, completion_time_seconds: float) -> float:
        """计算成本节约"""
        expert_cost = self.expert_time_hours * self.expert_hourly_rate_usd
        ai_cost = self._calculate_cost(self.token_usage["input"], self.token_usage["output"])
        return max(0.0, expert_cost - ai_cost)

class EfficiencyBenchmark:
    """效率基准测试器（使用外部标注数据）"""

    def __init__(self, annotation_base_dir: str = "data/annotation"):
        """
        初始化效率基准测试器

        Args:
            annotation_base_dir: 标注数据文件目录
        """
        self.annotation_loader = EnhancedAnnotationLoader(annotation_base_dir)
        self.results = []

    def evaluate_task(self,
                     task_id: str,
                     task_title: str,
                     task_type: str = "analysis_task",
                     expert_type: str = "senior_analyst",
                     model_name: str = "default",
                     task_function: callable = None,
                     **task_kwargs) -> EfficiencyMetrics:
        """
        评估单个任务的效率

        Args:
            task_id: 任务ID
            task_title: 任务标题
            task_type: 任务类型（用于查找专家时间）
            expert_type: 专家类型（用于查找时薪）
            model_name: 模型名称（用于查找token定价）
            task_function: 要执行的任务函数
            **task_kwargs: 传递给任务函数的参数

        Returns:
            EfficiencyMetrics: 效率评估结果
        """
        # 从标注数据获取专家基准数据
        expert_time = self.annotation_loader.get_task_type_expert_time(task_type)
        expert_rate = self.annotation_loader.get_expert_type_rate(expert_type)
        input_cost, output_cost = self.annotation_loader.get_token_pricing(model_name)

        # 创建评估器
        evaluator = EfficiencyEvaluator(
            expert_time_hours=expert_time,
            expert_hourly_rate_usd=expert_rate,
            token_cost_per_1k_input=input_cost,
            token_cost_per_1k_output=output_cost
        )

        # 开始评估
        evaluator.start_task(task_id, task_title)

        success = True
        try:
            if task_function:
                # 执行任务函数
                result = task_function(**task_kwargs)

                # 如果任务函数返回token使用信息，记录它
                if isinstance(result, dict) and "token_usage" in result:
                    token_usage = result["token_usage"]
                    evaluator.add_token_usage(
                        token_usage.get("input_tokens", 0),
                        token_usage.get("output_tokens", 0)
                    )
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            evaluator.add_error()
            success = False

        # 结束评估
        metrics = evaluator.end_task(success)
        self.results.append(metrics)

        return metrics

    def evaluate_batch(self,
                      tasks: List[Dict[str, Any]],
                      output_file: str = None) -> List[EfficiencyMetrics]:
        """
        批量评估任务效率

        Args:
            tasks: 任务列表，每个任务包含task_id, task_title, task_type等
            output_file: 结果输出文件路径

        Returns:
            List[EfficiencyMetrics]: 所有任务的效率评估结果
        """
        results = []

        for i, task in enumerate(tasks, 1):
            logger.info(f"评估任务 {i}/{len(tasks)}: {task.get('task_id', 'unknown')}")

            try:
                metrics = self.evaluate_task(**task)
                results.append(metrics)
            except Exception as e:
                logger.error(f"任务 {task.get('task_id')} 评估失败: {e}")

        # 保存结果
        if output_file:
            self.save_results(results, output_file)

        return results

    def save_results(self, results: List[EfficiencyMetrics], output_file: str):
        """保存评估结果到文件"""
        try:
            results_dict = [asdict(result) for result in results]

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)

            logger.info(f"效率评估结果已保存到: {output_file}")

        except Exception as e:
            logger.error(f"保存结果失败: {e}")

    def generate_efficiency_report(self, results: List[EfficiencyMetrics]) -> Dict[str, Any]:
        """生成效率评估报告"""
        if not results:
            return {"error": "没有可用的评估结果"}

        successful_tasks = [r for r in results if r.task_success]

        report = {
            "summary": {
                "total_tasks": len(results),
                "successful_tasks": len(successful_tasks),
                "success_rate": len(successful_tasks) / len(results) if results else 0,
                "total_errors": sum(r.error_count for r in results)
            },
            "time_metrics": {},
            "cost_metrics": {},
            "automation_metrics": {}
        }

        if successful_tasks:
            completion_times = [r.completion_time_seconds for r in successful_tasks]
            costs = [r.estimated_cost_usd for r in successful_tasks]
            savings = [r.cost_saving_usd for r in successful_tasks if r.cost_saving_usd]
            automation_rates = [r.automation_rate for r in successful_tasks if r.automation_rate]

            report["time_metrics"] = {
                "avg_completion_time_seconds": sum(completion_times) / len(completion_times),
                "min_completion_time_seconds": min(completion_times),
                "max_completion_time_seconds": max(completion_times),
                "total_time_seconds": sum(completion_times)
            }

            report["cost_metrics"] = {
                "avg_cost_usd": sum(costs) / len(costs),
                "total_cost_usd": sum(costs),
                "avg_cost_saving_usd": sum(savings) / len(savings) if savings else 0,
                "total_cost_saving_usd": sum(savings) if savings else 0
            }

            report["automation_metrics"] = {
                "avg_automation_rate": sum(automation_rates) / len(automation_rates) if automation_rates else 0,
                "min_automation_rate": min(automation_rates) if automation_rates else 0,
                "max_automation_rate": max(automation_rates) if automation_rates else 0
            }

        return report

    def get_annotation_statistics(self) -> Dict[str, Any]:
        """获取标注数据统计信息"""
        return self.annotation_loader.get_data_statistics()

if __name__ == "__main__":
    # 示例用法
    benchmark = EfficiencyBenchmark()

    # 验证标注数据
    if not benchmark.annotation_loader.validate_annotation_data():
        logger.error("标注数据验证失败")
        exit(1)

    # 打印标注数据统计
    stats = benchmark.get_annotation_statistics()
    logger.info(f"标注数据统计: {stats}")

    # 模拟任务评估
    def sample_task(**kwargs):
        """示例任务函数"""
        time.sleep(2)  # 模拟任务执行时间
        return {
            "result": "任务完成",
            "token_usage": {
                "input_tokens": 1000,
                "output_tokens": 500
            }
        }

    metrics = benchmark.evaluate_task(
        task_id="test_001",
        task_title="示例分析任务",
        task_type="analysis_task",
        expert_type="senior_analyst",
        model_name="gpt-3.5-turbo",
        task_function=sample_task
    )

    print(f"任务完成时间: {metrics.completion_time_seconds:.2f}秒")
    print(f"估算成本: ${metrics.estimated_cost_usd:.4f}")
    print(f"成本节约: ${metrics.cost_saving_usd:.2f}")
    print(f"自动化率: {metrics.automation_rate:.2%}")