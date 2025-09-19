#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POET Bench Query Selection System
This module provides functionality to evaluate and select high-value queries for the POET benchmark.
Based on the 7-dimensional query value assessment model.

Supported Input Formats:
1. Markdown (.md): Original format with specific query structure
2. CSV (.csv): Generic CSV format with required columns:
   - Required columns (case-insensitive, supports variants):
     * number/id/query_id/num/编号: Query identifier
     * title/query_title/name/subject/标题/题目: Query title
     * content/query/prompt/text/description/内容/查询/问题: Query content

   Example CSV format:
   number,title,content
   1,"Market Analysis","Analyze the current smartphone market trends"
   2,"Risk Assessment","Evaluate the financial risks of expanding to Europe"
"""

import re
import json
import csv
import os
import argparse
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv
from .api import AIClient
import pandas as pd

load_dotenv()

# Thread lock for protecting shared resources
print_lock = threading.Lock()

# Query evaluation criteria based on POET framework
SCORING_CRITERIA = {
    "A. 决策颠覆性": {
        "weight": 0.05,
        "description": "该问题的答案对最终商业决策的影响程度",
        "scale": "1. 参考级 -> 5. 决定性：答案从\"仅供参考\"的信息，到成为决策的核心依据和唯一理由。"
    },
    "B. 分析复杂性": {
        "weight": 0.20,
        "description": "解决问题所需的认知复杂度与步骤",
        "scale": "1. 简单检索 -> 5. 多维建模：从单点查询，到需要交叉验证、建立量化模型、进行逻辑推演。"
    },
    "C. 行动导向性": {
        "weight": 0.20,
        "description": "答案的可执行程度，能否直接转化为行动",
        "scale": "1. 描述性 -> 5. 可执行：答案从一段文字描述，到一个包含步骤、清单、模型或完整方案的可行动输出。"
    },
    "D. 风险/收益规模": {
        "weight": 0.15,
        "description": "该问题背后所关联的潜在商业收益或风险损失的大小",
        "scale": "1. 微不足道 -> 5. 战略级：关联的财务影响从可忽略不计，到影响公司数亿资金流向或存亡。"
    },
    "E. 时效敏感性": {
        "weight": 0.10,
        "description": "答案对信息新鲜度的依赖程度",
        "scale": "1. 静态知识 -> 5. 实时情报：从基于历史事实，到极度依赖24小时内的动态信息（如股价、舆情、政策）。"
    },
    "F. 专业壁垒": {
        "weight": 0.05,
        "description": "解决问题所需知识的专业性和稀缺性",
        "scale": "1. 通用知识 -> 5. 尖端领域：从常识，到需要深度的、鲜为人知的领域专业知识（如特定专利法条、临床诊疗指南）。"
    },
    "G. 可验证性": {
        "weight": 0.25,
        "description": "答案正确与否是否易于被人类专家快速验证",
        "scale": "1. 难以验证 -> 5. 极易验证：从输出一个主观的模糊观点、涉及价值判断、推断的，到输出带有数据源、计算、推理过程、法律条文引用的确定的可验证答案。"
    }
}

def extract_queries_from_markdown(file_path: str) -> List[Dict[str, str]]:
    """从markdown文件中提取所有query"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    queries = []

    # 支持多种query格式的正则表达式
    pattern = r'#### \*\*Query\*\* \*\*(\d+): ([^*]+)\*\*\s*\n\n"([^"]+)"|#### \*\*Query (\d+): ([^*]+)\*\*\s*\n\n"([^"]+)"'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        if match[0]:  # Format 1
            query_num, title, content_text = match[0], match[1], match[2]
        else:  # Format 2
            query_num, title, content_text = match[3], match[4], match[5]

        queries.append({
            "number": int(query_num),
            "title": title.strip(),
            "content": content_text.strip()
        })

    return queries

def extract_queries_from_csv(file_path: str) -> List[Dict[str, str]]:
    """从CSV文件中提取所有query

    CSV格式要求:
    - 必须包含列: number, title, content (或 query, 或 prompt)
    - 可选列: id (如果没有number列)
    """
    queries = []

    try:
        # 尝试不同的编码
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise ValueError(f"无法以任何编码读取CSV文件: {file_path}")

        # 检查必需的列
        required_columns = set(['number', 'title', 'content'])
        available_columns = set(df.columns.str.lower())

        # 列名映射 - 支持常见的列名变体
        column_mapping = {
            'number': ['number', 'id', 'query_id', 'num', '编号'],
            'title': ['title', 'query_title', 'name', 'subject', '标题', '题目'],
            'content': ['content', 'query', 'prompt', 'text', 'description', '内容', '查询', '问题']
        }

        # 找到实际的列名
        actual_columns = {}
        for standard_name, variants in column_mapping.items():
            found = False
            for variant in variants:
                if variant.lower() in available_columns:
                    actual_columns[standard_name] = variant
                    found = True
                    break
            if not found:
                raise ValueError(f"CSV文件缺少必需的列: {standard_name} (支持的列名: {', '.join(variants)})")

        # 提取数据
        for index, row in df.iterrows():
            try:
                # 获取编号，如果number列是数字则使用，否则使用行索引+1
                number_value = row[actual_columns['number']]
                if pd.isna(number_value):
                    number = index + 1
                else:
                    try:
                        number = int(number_value)
                    except (ValueError, TypeError):
                        number = index + 1

                title = str(row[actual_columns['title']]).strip()
                content = str(row[actual_columns['content']]).strip()

                # 跳过空行
                if not title or title.lower() in ['nan', 'none'] or not content or content.lower() in ['nan', 'none']:
                    continue

                queries.append({
                    "number": number,
                    "title": title,
                    "content": content
                })

            except Exception as e:
                print(f"警告: 跳过第{index+1}行，解析失败: {str(e)}")
                continue

        if not queries:
            raise ValueError("CSV文件中没有找到有效的查询数据")

        print(f"从CSV文件成功读取 {len(queries)} 个查询")
        return queries

    except Exception as e:
        raise ValueError(f"读取CSV文件失败: {str(e)}")

def extract_queries(file_path: str) -> List[Dict[str, str]]:
    """根据文件扩展名自动选择提取方法"""
    file_ext = os.path.splitext(file_path.lower())[1]

    if file_ext == '.csv':
        return extract_queries_from_csv(file_path)
    elif file_ext == '.md':
        return extract_queries_from_markdown(file_path)
    else:
        # 尝试根据内容判断
        try:
            # 先尝试CSV
            return extract_queries_from_csv(file_path)
        except:
            try:
                # 再尝试Markdown
                return extract_queries_from_markdown(file_path)
            except:
                raise ValueError(f"不支持的文件格式: {file_ext}。支持的格式: .csv, .md")

def create_scoring_prompt(query: Dict[str, str]) -> str:
    """创建评分提示词"""
    prompt = f"""我正在构建一个以"价值交付"为导向的AI智能体评估基准的问题集，请根据以下7个维度对以下query进行评分（1-5分），来让我能够筛选最能为客户提供商业价值的query：

Query {query['number']}: {query['title']}
内容: {query['content']}

评分标准：
"""

    for criterion, details in SCORING_CRITERIA.items():
        prompt += f"""
{criterion} (权重: {details['weight']*100}%):
描述: {details['description']}
评分标准: {details['scale']}
"""

    prompt += """
请为每个维度给出1-5分的评分，并简要说明评分理由。请以JSON格式输出结果：
{
    "scores": {
        "A. 决策颠覆性": {"score": X, "reason": "..."},
        "B. 分析复杂性": {"score": X, "reason": "..."},
        "C. 行动导向性": {"score": X, "reason": "..."},
        "D. 风险/收益规模": {"score": X, "reason": "..."},
        "E. 时效敏感性": {"score": X, "reason": "..."},
        "F. 专业壁垒": {"score": X, "reason": "..."},
        "G. 可验证性": {"score": X, "reason": "..."}
    }
}"""

    return prompt

def call_llm_for_scoring(prompt: str, ai_client: AIClient) -> Dict[str, Any]:
    """调用大模型进行评分"""
    try:
        response = ai_client.generate(prompt)

        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)

                # 计算overall_score
                if "scores" in result:
                    overall_score = calculate_weighted_score(result["scores"])
                    result["overall_score"] = round(overall_score, 2)

                return result
            else:
                return {"error": "无法找到有效的JSON响应"}
        except json.JSONDecodeError:
            return {"error": f"JSON解析失败: {response}"}

    except Exception as e:
        return {"error": f"API调用失败: {str(e)}"}

def calculate_weighted_score(scores: Dict[str, Dict[str, Any]]) -> float:
    """计算加权总分"""
    total_score = 0.0
    total_weight = 0.0

    for criterion, details in SCORING_CRITERIA.items():
        if criterion in scores and "score" in scores[criterion]:
            score = scores[criterion]["score"]
            weight = details["weight"]
            total_score += score * weight
            total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0.0

def process_single_query(query: Dict[str, str], query_index: int, total_queries: int, ai_client: AIClient) -> Dict[str, Any]:
    """处理单个query的评分"""
    with print_lock:
        print(f"\n正在处理 Query {query['number']}: {query['title']} ({query_index}/{total_queries})")

    try:
        # 创建评分提示词
        prompt = create_scoring_prompt(query)

        # 调用大模型评分
        scoring_result = call_llm_for_scoring(prompt, ai_client)

        if "error" in scoring_result:
            with print_lock:
                print(f"Query {query['number']} 评分失败: {scoring_result['error']}")
            return None

        # 构建结果
        result = {
            "query_number": query["number"],
            "query_title": query["title"],
            "query_content": query["content"],
            "scoring_result": scoring_result
        }

        with print_lock:
            print(f"Query {query['number']} 评分完成，总分: {scoring_result.get('overall_score', 'N/A')}")

        return result

    except Exception as e:
        with print_lock:
            print(f"Query {query['number']} 处理异常: {str(e)}")
        return None

def save_results_to_csv(results: List[Dict[str, Any]], output_file: str = "query_scores.csv"):
    """将结果保存为CSV格式"""
    valid_results = [r for r in results if "overall_score" in r["scoring_result"]]

    if not valid_results:
        print("没有有效的评分结果可保存")
        return

    # 按分数排序
    valid_results.sort(key=lambda x: x["scoring_result"]["overall_score"], reverse=True)

    # 定义CSV列
    fieldnames = [
        "排名", "Query编号", "Query标题", "总分",
        "A.决策颠覆性", "B.分析复杂性", "C.行动导向性",
        "D.风险收益规模", "E.时效敏感性", "F.专业壁垒", "G.可验证性",
        "Query内容"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, result in enumerate(valid_results, 1):
            scoring_result = result["scoring_result"]
            scores = scoring_result.get("scores", {})

            row = {
                "排名": i,
                "Query编号": result["query_number"],
                "Query标题": result["query_title"],
                "Query内容": result["query_content"],
                "总分": scoring_result.get("overall_score", 0),
                "A.决策颠覆性": scores.get("A. 决策颠覆性", {}).get("score", 0),
                "B.分析复杂性": scores.get("B. 分析复杂性", {}).get("score", 0),
                "C.行动导向性": scores.get("C. 行动导向性", {}).get("score", 0),
                "D.风险收益规模": scores.get("D. 风险/收益规模", {}).get("score", 0),
                "E.时效敏感性": scores.get("E. 时效敏感性", {}).get("score", 0),
                "F.专业壁垒": scores.get("F. 专业壁垒", {}).get("score", 0),
                "G.可验证性": scores.get("G. 可验证性", {}).get("score", 0)
            }
            writer.writerow(row)

    print(f"CSV结果已保存到 {output_file}")

def filter_high_value_queries(results: List[Dict[str, Any]], threshold: float = 4.0) -> List[Dict[str, Any]]:
    """筛选高价值queries (总分 >= threshold)"""
    valid_results = [r for r in results if "overall_score" in r["scoring_result"]]
    high_value_queries = [r for r in valid_results if r["scoring_result"]["overall_score"] >= threshold]

    # 按分数降序排序
    high_value_queries.sort(key=lambda x: x["scoring_result"]["overall_score"], reverse=True)

    return high_value_queries

def export_selected_queries_to_jsonl(selected_queries: List[Dict[str, Any]], output_file: str):
    """将筛选后的queries导出为标准的benchmark格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, query_data in enumerate(selected_queries):
            benchmark_entry = {
                "id": f"query_{query_data['query_number']:03d}",
                "domain": "research",  # 可以根据需要分类
                "complexity_level": min(5, max(1, int(query_data['scoring_result']['overall_score']))),
                "prompt": query_data['query_content'],
                "query_metadata": {
                    "title": query_data['query_title'],
                    "original_number": query_data['query_number'],
                    "poet_score": query_data['scoring_result']['overall_score'],
                    "scoring_breakdown": query_data['scoring_result']['scores']
                }
            }
            f.write(json.dumps(benchmark_entry, ensure_ascii=False) + '\n')

    print(f"筛选的查询已导出到 {output_file}")

def determine_topic(query_title: str, query_content: str) -> str:
    """Determine topic category based on query content"""
    content_lower = (query_title + " " + query_content).lower()

    # Define keyword mappings to topics
    topic_keywords = {
        "Finance & Business": ["投资", "金融", "资金", "收入", "财务", "保险", "银行", "股票", "基金", "融资", "经济", "商业", "市场", "价格"],
        "Technology": ["技术", "软件", "算法", "程序", "数据", "网络", "系统", "开发", "编程", "计算机", "人工智能", "ai"],
        "Healthcare & Medicine": ["医疗", "健康", "药物", "医院", "病", "治疗", "药械", "医学", "疫苗", "诊断", "临床"],
        "Law & Policy": ["法律", "政策", "法规", "条例", "法院", "合规", "监管", "政府", "行政", "法条", "豁免", "申请流程"],
        "Education": ["教育", "学校", "学习", "培训", "课程", "教学", "研究", "大学", "学生", "考试"],
        "Science & Research": ["研究", "科学", "实验", "数据", "分析", "模型", "理论", "方法", "技术"],
        "Industry & Manufacturing": ["工业", "制造", "生产", "工厂", "供应链", "材料", "设备", "机械"],
        "General Research": ["其他", "综合", "一般"]
    }

    # Check which topic has the most matching keywords
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            topic_scores[topic] = score

    if topic_scores:
        return max(topic_scores.items(), key=lambda x: x[1])[0]
    else:
        return "General Research"

def determine_language(query_content: str) -> str:
    """Determine language based on query content"""
    # Simple heuristic: if contains Chinese characters, it's Chinese
    for char in query_content:
        if '\u4e00' <= char <= '\u9fff':  # Chinese Unicode range
            return "zh"
    return "en"

def convert_to_benchmark_jsonl(query_scores: List[Dict[str, Any]],
                              score_threshold: float = 0.0,
                              output_file: str = None) -> List[Dict[str, Any]]:
    """Convert query scores to benchmark JSONL format"""

    # Filter queries based on threshold and sort by score
    if score_threshold > 0:
        filtered_queries = [
            q for q in query_scores
            if "overall_score" in q["scoring_result"] and
               q["scoring_result"]["overall_score"] >= score_threshold
        ]
    else:
        # Use all queries if threshold is 0
        filtered_queries = [
            q for q in query_scores
            if "overall_score" in q["scoring_result"]
        ]

    # Sort by score descending
    filtered_queries.sort(
        key=lambda x: x["scoring_result"]["overall_score"],
        reverse=True
    )

    converted_queries = []

    for i, query_data in enumerate(filtered_queries, 1):
        # Extract basic info
        query_title = query_data["query_title"]
        query_content = query_data["query_content"]

        # Determine topic and language
        topic = determine_topic(query_title, query_content)
        language = determine_language(query_content)

        # Create JSONL entry (clean format for benchmark)
        jsonl_entry = {
            "id": i,
            "topic": topic,
            "language": language,
            "prompt": query_content
        }

        converted_queries.append(jsonl_entry)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in converted_queries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"转换后的benchmark格式已保存到 {output_file}")
        print(f"共保存 {len(converted_queries)} 个查询")

    return converted_queries

def filter_and_convert_from_scores(scores_file: str, threshold: float, output_file: str):
    """从已有的query_scores.json文件中筛选并转换格式"""
    print(f"从缓存的评分文件筛选: {scores_file}")
    print(f"使用阈值: {threshold}")

    try:
        with open(scores_file, 'r', encoding='utf-8') as f:
            query_scores = json.load(f)

        # 转换为benchmark格式
        convert_to_benchmark_jsonl(query_scores, threshold, output_file)

        # 统计信息
        filtered_count = len([q for q in query_scores
                            if "overall_score" in q["scoring_result"] and
                            q["scoring_result"]["overall_score"] >= threshold])
        total_count = len([q for q in query_scores if "overall_score" in q["scoring_result"]])

        print(f"筛选结果: {filtered_count}/{total_count} 个查询 (阈值≥{threshold})")

    except Exception as e:
        print(f"处理失败: {str(e)}")
        raise

def generate_criteria_from_scores(scores_file: str, criteria_output: str = "data/criteria_data/criteria.jsonl"):
    """从评分文件生成动态评估标准"""
    print(f"从评分文件生成criteria: {scores_file}")

    try:
        # 读取评分结果
        with open(scores_file, 'r', encoding='utf-8') as f:
            query_scores = json.load(f)

        # 生成criteria（简化版实现）
        criteria_results = []
        valid_queries = [q for q in query_scores if "overall_score" in q["scoring_result"]]

        for i, query_data in enumerate(valid_queries, 1):
            # 为每个query生成基本的criteria结构
            criteria_entry = {
                "id": i,
                "prompt": query_data["query_content"],
                "dimension_weight": {
                    "comprehensiveness": 0.25,
                    "insight": 0.25,
                    "instruction_following": 0.25,
                    "readability": 0.25
                },
                "criterions": {
                    "comprehensiveness": [
                        {"criterion": "信息覆盖面", "explanation": "评估回答的信息覆盖面和完整性", "weight": 1.0}
                    ],
                    "insight": [
                        {"criterion": "深度分析", "explanation": "评估分析的深度和洞察力", "weight": 1.0}
                    ],
                    "instruction_following": [
                        {"criterion": "指令遵循", "explanation": "评估对查询指令的遵循程度", "weight": 1.0}
                    ],
                    "readability": [
                        {"criterion": "可读性", "explanation": "评估文本的清晰度和可读性", "weight": 1.0}
                    ]
                }
            }

            criteria_results.append(criteria_entry)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(criteria_output), exist_ok=True)

        # 保存结果
        with open(criteria_output, 'w', encoding='utf-8') as f:
            for result in criteria_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

        print(f"动态criteria已保存到 {criteria_output}")
        print(f"成功生成 {len(criteria_results)} 个criteria项目")

    except Exception as e:
        print(f"Criteria生成失败: {str(e)}")
        raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="POET Bench Query Selection System")
    parser.add_argument("--input_file", default="data/query_analysis/raw_query.md",
                        help="Input file containing queries (supports .md and .csv formats)")
    parser.add_argument("--output_dir", default="data/query_analysis/",
                        help="Output directory for results")
    parser.add_argument("--threshold", type=float, default=4.0,
                        help="Minimum score threshold for selected queries")
    parser.add_argument("--max_workers", type=int, default=8,
                        help="Maximum number of worker threads")
    parser.add_argument("--export_selected", action="store_true",
                        help="Export selected high-value queries to benchmark format")
    parser.add_argument("--from_scores", type=str,
                        help="Use existing scores file instead of re-evaluating (path to query_scores.json)")
    parser.add_argument("--convert_to_jsonl", type=str,
                        help="Convert and filter to benchmark JSONL format (output file path)")

    args = parser.parse_args()

    print("=== POET Bench Query Selection System ===")

    # 检查是否使用缓存的评分文件
    if args.from_scores:
        if not os.path.exists(args.from_scores):
            print(f"错误: 指定的评分文件不存在: {args.from_scores}")
            return

        print("使用缓存的评分文件进行筛选...")

        if args.convert_to_jsonl:
            # 直接从评分文件筛选并转换为benchmark格式
            filter_and_convert_from_scores(args.from_scores, args.threshold, args.convert_to_jsonl)
        else:
            print("错误: 使用 --from_scores 时必须指定 --convert_to_jsonl 输出文件")
        return

    print("开始提取和评分queries...")

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 提取queries
    if not os.path.exists(args.input_file):
        print(f"错误：找不到输入文件 {args.input_file}")
        return

    queries = extract_queries(args.input_file)
    print(f"共找到 {len(queries)} 个queries")

    if not queries:
        print("没有找到任何queries，请检查输入文件格式")
        return

    # 初始化AI客户端
    ai_client = AIClient()

    print(f"使用 {args.max_workers} 个线程并发处理...")

    results = []
    start_time = time.time()

    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # 提交所有任务
        future_to_query = {
            executor.submit(process_single_query, query, i+1, len(queries), ai_client): query
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

    print(f"\n所有评分完成！总耗时: {processing_time:.2f}秒")

    # 保存完整结果到JSON文件
    json_output_file = os.path.join(args.output_dir, "query_scores.json")
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"JSON结果已保存到 {json_output_file}")

    # 保存结果到CSV文件
    csv_output_file = os.path.join(args.output_dir, "query_scores.csv")
    save_results_to_csv(results, csv_output_file)

    # 筛选高价值queries
    selected_queries = filter_high_value_queries(results, args.threshold)

    print(f"\n=== 筛选结果 ===")
    print(f"阈值: {args.threshold}分")
    print(f"筛选出 {len(selected_queries)} 个高价值queries (占比: {len(selected_queries)/len(results)*100:.1f}%)")

    if args.export_selected and selected_queries:
        selected_output_file = os.path.join(args.output_dir, "selected_queries.jsonl")
        export_selected_queries_to_jsonl(selected_queries, selected_output_file)

    # 生成汇总报告
    print("\n=== 评分汇总报告 ===")
    valid_results = [r for r in results if "overall_score" in r["scoring_result"]]

    if valid_results:
        # 按分数排序
        valid_results.sort(key=lambda x: x["scoring_result"]["overall_score"], reverse=True)

        print(f"\n前10个最高分的queries:")
        for i, result in enumerate(valid_results[:10], 1):
            score = result["scoring_result"]["overall_score"]
            print(f"{i:2d}. Query {result['query_number']:2d}: {result['query_title']} (总分: {score:.2f})")

        # 统计信息
        scores = [r["scoring_result"]["overall_score"] for r in valid_results]
        print(f"\n统计信息:")
        print(f"平均分: {sum(scores)/len(scores):.2f}")
        print(f"最高分: {max(scores):.2f}")
        print(f"最低分: {min(scores):.2f}")
        print(f"成功处理: {len(valid_results)}/{len(queries)} 个queries")
        print(f"平均每个query耗时: {processing_time/len(queries):.2f}秒")

        # 筛选统计
        if selected_queries:
            print(f"\n高价值查询统计 (≥{args.threshold}分):")
            for i, result in enumerate(selected_queries[:5], 1):
                score = result["scoring_result"]["overall_score"]
                print(f"{i}. Query {result['query_number']:2d}: {result['query_title']} ({score:.2f}分)")

if __name__ == "__main__":
    main()
