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

def process_single_query(query: Dict[str, Any], query_index: int, total_queries: int) -> Dict[str, Any]:
    """处理单个query的rubrics生成"""
    with print_lock:
        print(f"\n正在处理 Query {query['number']}: {query['title']} ({query_index}/{total_queries})")
    
    try:
        result = {
            "query_number": query["number"],
            "query_title": query["title"],
            "query_content": query["content"],
            "overall_score": query["overall_score"],
            "dimension_weights": {},
            "criteria": {}
        }
        
        # 1. 生成维度权重
        with print_lock:
            print(f"  - 生成维度权重...")
        weights_result = generate_dimension_weights(query)
        if "error" in weights_result:
            result["error"] = weights_result["error"]
            return result
        
        result["dimension_weights"] = weights_result["weights"]
        result["weights_analysis"] = weights_result["analysis"]
        
        # 2. 为每个维度生成评判标准
        dimensions = ["comprehensiveness", "insight", "instruction_following", "readability"]
        for dimension in dimensions:
            with print_lock:
                print(f"  - 生成{dimension}维度标准...")
            
            criteria_result = generate_criteria_for_dimension(query, dimension)
            if "error" in criteria_result:
                result[f"{dimension}_error"] = criteria_result["error"]
            else:
                result["criteria"][dimension] = criteria_result
        
        with print_lock:
            print(f"Query {query['number']} rubrics生成完成")
        
        return result
        
    except Exception as e:
        with print_lock:
            print(f"Query {query['number']} 处理异常: {str(e)}")
        return {"error": f"处理异常: {str(e)}"}

def save_results_to_json(results: List[Dict[str, Any]], output_file: str = "query_rubrics.json"):
    """将结果保存为JSON格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON结果已保存到 {output_file}")

def save_results_to_csv(results: List[Dict[str, Any]], output_file: str = "query_rubrics.csv"):
    """将结果保存为CSV格式"""
    # 准备CSV数据
    csv_data = []
    
    for result in results:
        if "error" in result:
            continue
            
        base_row = {
            "Query编号": result["query_number"],
            "Query标题": result["query_title"],
            "Query内容": result["query_content"],
            "总分": result["overall_score"]
        }
        
        # 添加维度权重
        weights = result.get("dimension_weights", {})
        base_row.update({
            "全面性权重": weights.get("comprehensiveness", 0),
            "洞察力权重": weights.get("insight", 0),
            "指令遵循权重": weights.get("instruction_following", 0),
            "可读性权重": weights.get("readability", 0)
        })
        
        # 添加权重分析
        base_row["权重分析"] = result.get("weights_analysis", "")
        
        # 添加各维度的评判标准数量
        criteria = result.get("criteria", {})
        for dimension in ["comprehensiveness", "insight", "instruction_following", "readability"]:
            if dimension in criteria and isinstance(criteria[dimension], list):
                base_row[f"{dimension}_标准数量"] = len(criteria[dimension])
            else:
                base_row[f"{dimension}_标准数量"] = 0
        
        csv_data.append(base_row)
    
    # 保存CSV
    if csv_data:
        df = pd.DataFrame(csv_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"CSV结果已保存到 {output_file}")
    else:
        print("没有有效数据可保存到CSV")

def main():
    """主函数"""
    print("开始读取CSV文件并生成rubrics...")
    
    # 读取queries
    queries = read_queries_from_csv("query_scores.csv")
    if not queries:
        print("没有找到有效的queries，程序退出")
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
            executor.submit(process_single_query, query, i+1, len(queries)): query 
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
    
    print(f"\n所有rubrics生成完成！总耗时: {processing_time:.2f}秒")
    
    # 保存结果
    save_results_to_json(results, "query_rubrics.json")
    save_results_to_csv(results, "query_rubrics.csv")
    
    # 生成汇总报告
    print("\n=== Rubrics生成汇总报告 ===")
    valid_results = [r for r in results if "error" not in r]
    
    if valid_results:
        print(f"成功生成: {len(valid_results)}/{len(queries)} 个queries的rubrics")
        print(f"平均每个query耗时: {processing_time/len(queries):.2f}秒")
        
        # 统计各维度的标准数量
        total_criteria = {"comprehensiveness": 0, "insight": 0, "instruction_following": 0, "readability": 0}
        for result in valid_results:
            criteria = result.get("criteria", {})
            for dimension in total_criteria:
                if dimension in criteria and isinstance(criteria[dimension], list):
                    total_criteria[dimension] += len(criteria[dimension])
        
        print(f"\n各维度评判标准统计:")
        for dimension, count in total_criteria.items():
            avg_count = count / len(valid_results) if valid_results else 0
            print(f"  {dimension}: 总计 {count} 条，平均 {avg_count:.1f} 条/query")
    else:
        print("没有成功生成任何rubrics")

if __name__ == "__main__":
    main() 