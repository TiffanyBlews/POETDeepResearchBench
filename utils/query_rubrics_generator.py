#!/usr/bin/env python3
"""
Query-specific Dynamic Criteria Generator for POET Bench

This module generates query-specific evaluation criteria directly in the standard
criteria.jsonl format, eliminating the need for format conversion.

Features:
- Reads query scores from CSV and query mapping from JSONL
- Generates dynamic dimension weights using LLM
- Creates detailed evaluation criteria for each dimension
- Outputs directly to data/criteria_data/criteria.jsonl format
"""

import pandas as pd
import json
import re
from openai import OpenAI
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import os
from dotenv import load_dotenv
load_dotenv()

# 导入criteria_prompt_zh.py中的prompt模板
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prompt.criteria_prompt_zh import (
    generate_eval_dimension_weight_prompt,
    generate_eval_criteria_prompt_comp,
    generate_eval_criteria_prompt_insight,
    generate_eval_criteria_prompt_Inst,
    generate_eval_criteria_prompt_readability
)

# 初始化OpenAI客户端
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1'),
    api_key=os.getenv('OPENAI_API_KEY'),
)

# 线程锁，用于保护共享资源
print_lock = threading.Lock()

def read_queries_from_csv(csv_file: str) -> List[Dict[str, Any]]:
    """从CSV文件中读取queries"""
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        queries = []

        for _, row in df.iterrows():
            queries.append({
                "number": row["Query编号"],
                "title": row["Query标题"],
                "content": row["Query内容"],
                "overall_score": row["总分"]
            })

        print(f"成功读取 {len(queries)} 个queries")
        return queries
    except Exception as e:
        print(f"读取CSV文件失败: {str(e)}")
        return []

def read_query_mapping(query_file: str) -> Dict[str, Dict[str, Any]]:
    """从query.jsonl文件中读取id映射"""
    query_mapping = {}
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    query_item = json.loads(line)
                    query_mapping[query_item['prompt']] = query_item
        print(f"成功读取 {len(query_mapping)} 个query映射")
        return query_mapping
    except Exception as e:
        print(f"读取query映射失败: {str(e)}")
        return {}

def extract_json_from_response(response: str) -> Dict[str, Any]:
    """从响应中提取JSON内容"""
    try:
        # 尝试找到JSON部分
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        else:
            return {"error": "无法找到有效的JSON响应"}
    except json.JSONDecodeError:
        return {"error": f"JSON解析失败: {response}"}

def call_llm_for_rubrics(prompt: str) -> Dict[str, Any]:
    """调用大模型生成rubrics"""
    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.5-pro",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        return extract_json_from_response(response)
        
    except Exception as e:
        return {"error": f"API调用失败: {str(e)}"}

def generate_dimension_weights(query: Dict[str, Any]) -> Dict[str, Any]:
    """生成维度权重"""
    prompt = generate_eval_dimension_weight_prompt.format(task_prompt=query["content"])
    result = call_llm_for_rubrics(prompt)
    
    if "error" in result:
        return result
    
    # 提取权重信息
    weights = {}
    if "comprehensiveness" in result:
        weights["comprehensiveness"] = result["comprehensiveness"]
    if "insight" in result:
        weights["insight"] = result["insight"]
    if "instruction_following" in result:
        weights["instruction_following"] = result["instruction_following"]
    if "readability" in result:
        weights["readability"] = result["readability"]
    
    return {"weights": weights, "analysis": result.get("analysis", "")}

def generate_criteria_for_dimension(query: Dict[str, Any], dimension: str) -> Dict[str, Any]:
    """为特定维度生成评判标准"""
    prompt_templates = {
        "comprehensiveness": generate_eval_criteria_prompt_comp,
        "insight": generate_eval_criteria_prompt_insight,
        "instruction_following": generate_eval_criteria_prompt_Inst,
        "readability": generate_eval_criteria_prompt_readability
    }
    
    if dimension not in prompt_templates:
        return {"error": f"未知的维度: {dimension}"}
    
    prompt = prompt_templates[dimension].format(task_prompt=query["content"])
    result = call_llm_for_rubrics(prompt)
    
    if "error" in result:
        return result
    
    return result

def process_single_query(query: Dict[str, Any], query_index: int, total_queries: int, query_mapping: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """处理单个query的criteria生成"""
    with print_lock:
        print(f"\n正在处理 Query {query['number']}: {query['title']} ({query_index}/{total_queries})")

    try:
        # 查找对应的query ID
        matching_query = None
        for prompt, qdata in query_mapping.items():
            if (query['content'] in prompt or prompt in query['content'] or
                str(qdata.get('id', '')) == str(query['number'])):
                matching_query = qdata
                break

        if not matching_query:
            print(f"Warning: 无法找到Query {query['number']}的对应ID")
            return {"error": f"无法找到Query {query['number']}的对应ID"}

        # 1. 生成维度权重
        with print_lock:
            print(f"  - 生成维度权重...")
        weights_result = generate_dimension_weights(query)
        if "error" in weights_result:
            return {"error": weights_result["error"]}

        # 2. 为每个维度生成评判标准
        criteria_result = {}
        dimensions = ["comprehensiveness", "insight", "instruction_following", "readability"]
        for dimension in dimensions:
            with print_lock:
                print(f"  - 生成{dimension}维度标准...")

            dimension_criteria = generate_criteria_for_dimension(query, dimension)
            if "error" in dimension_criteria:
                print(f"  - {dimension}维度生成失败: {dimension_criteria['error']}")
                criteria_result[dimension] = [{
                    "criterion": f"Default {dimension} criterion",
                    "explanation": f"Default explanation for {dimension}",
                    "weight": 1.0
                }]
            else:
                criteria_result[dimension] = dimension_criteria

        # 3. 构建criteria格式的结果
        result = {
            "id": matching_query['id'],
            "prompt": matching_query['prompt'],
            "dimension_weight": weights_result["weights"],
            "criterions": criteria_result
        }

        with print_lock:
            print(f"Query {query['number']} criteria生成完成")

        return result

    except Exception as e:
        with print_lock:
            print(f"Query {query['number']} 处理异常: {str(e)}")
        return {"error": f"处理异常: {str(e)}"}

def save_results_to_jsonl(results: List[Dict[str, Any]], output_file: str = "data/criteria_data/criteria.jsonl"):
    """将结果保存为JSONL格式（criteria标准格式）"""
    # 筛选有效结果并按ID排序
    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x['id'])

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for result in valid_results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"Criteria结果已保存到 {output_file}")
    print(f"成功转换 {len(valid_results)} 个criteria项目")

def main():
    """主函数"""
    print("开始读取CSV文件并生成criteria...")

    # 读取queries
    queries = read_queries_from_csv("data/query_analysis/query_scores.csv")
    if not queries:
        print("没有找到有效的queries，程序退出")
        return

    # 读取query映射
    query_mapping = read_query_mapping("data/prompt_data/query.jsonl")
    if not query_mapping:
        print("没有找到有效的query映射，程序退出")
        return

    # 设置线程数（可以根据API限制调整）
    max_workers = 8 # 减少线程数，因为每个query需要多次API调用

    print(f"使用 {max_workers} 个线程并发处理...")

    results = []
    start_time = time.time()

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_query = {
            executor.submit(process_single_query, query, i+1, len(queries), query_mapping): query
            for i, query in enumerate(queries)
        }

        # 收集结果
        completed_count = 0
        for future in as_completed(future_to_query):
            completed_count += 1
            result = future.result()

            if result is not None:
                results.append(result)

            # 显示进度
            with print_lock:
                print(f"进度: {completed_count}/{len(queries)} 完成")

    end_time = time.time()
    processing_time = end_time - start_time

    print(f"\n所有criteria生成完成！总耗时: {processing_time:.2f}秒")

    # 保存结果为JSONL格式
    save_results_to_jsonl(results, "data/criteria_data/criteria.jsonl")

    # 生成汇总报告
    print("\n=== Criteria生成汇总报告 ===")
    valid_results = [r for r in results if "error" not in r]

    if valid_results:
        print(f"成功生成: {len(valid_results)}/{len(queries)} 个queries的criteria")
        print(f"平均每个query耗时: {processing_time/len(queries):.2f}秒")

        # 统计各维度的标准数量
        total_criteria = {"comprehensiveness": 0, "insight": 0, "instruction_following": 0, "readability": 0}
        for result in valid_results:
            criterions = result.get("criterions", {})
            for dimension in total_criteria:
                if dimension in criterions and isinstance(criterions[dimension], list):
                    total_criteria[dimension] += len(criterions[dimension])

        print(f"\n各维度评判标准统计:")
        for dimension, count in total_criteria.items():
            avg_count = count / len(valid_results) if valid_results else 0
            print(f"  {dimension}: 总计 {count} 条，平均 {avg_count:.1f} 条/query")
    else:
        print("没有成功生成任何criteria")

if __name__ == "__main__":
    main() 