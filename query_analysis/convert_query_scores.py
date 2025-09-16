#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert query_scores.json to query.jsonl format
Transforms POET query scoring results into the standard benchmark format
"""

import json
import argparse
import os
from typing import List, Dict, Any

def load_query_scores(file_path: str) -> List[Dict[str, Any]]:
    """Load query scores from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

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
        "Real Estate & Construction": ["房地产", "建筑", "房价", "土地", "开发", "物业", "装修", "建设"],
        "Transportation & Logistics": ["交通", "物流", "运输", "汽车", "航空", "铁路", "船舶", "配送"],
        "Energy & Environment": ["能源", "环境", "电力", "石油", "天然气", "污染", "节能", "环保", "气候"],
        "Entertainment & Media": ["娱乐", "媒体", "电影", "音乐", "游戏", "体育", "新闻", "广告"],
        "Agriculture & Food": ["农业", "食品", "种植", "养殖", "农产品", "食物", "餐饮"],
        "Tourism & Hospitality": ["旅游", "酒店", "景点", "度假", "民宿", "餐厅"]
    }

    # Count keyword matches for each topic
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            topic_scores[topic] = score

    # Return topic with highest score, default to "General Research"
    if topic_scores:
        return max(topic_scores, key=topic_scores.get)
    else:
        return "General Research"

def determine_language(query_content: str) -> str:
    """Determine language based on query content"""
    # Simple heuristic: if contains Chinese characters, it's Chinese
    for char in query_content:
        if '\u4e00' <= char <= '\u9fff':  # Chinese Unicode range
            return "zh"
    return "en"

def convert_to_jsonl_format(query_scores: List[Dict[str, Any]],
                           score_threshold: float = 0.0) -> List[Dict[str, Any]]:
    """Convert query scores to JSONL format"""

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

    return converted_queries

def save_as_jsonl(queries: List[Dict[str, Any]], output_file: str):
    """Save queries as JSONL file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for query in queries:
            f.write(json.dumps(query, ensure_ascii=False) + '\n')

    print(f"已保存 {len(queries)} 个查询到 {output_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Convert query_scores.json to query.jsonl format")
    parser.add_argument("--input_file",
                        default="query_analysis/query_scores.json",
                        help="Input query scores JSON file")
    parser.add_argument("--output_file",
                        default="data/prompt_data/selected_query.jsonl",
                        help="Output JSONL file")
    parser.add_argument("--score_threshold",
                        type=float,
                        default=0.0,
                        help="Minimum POET score threshold (0.0 = include all queries)")
    parser.add_argument("--backup_original",
                        action="store_true",
                        help="Backup original query.jsonl file")

    args = parser.parse_args()

    print("=== Query Scores to JSONL Converter ===")

    # Check input file exists
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在: {args.input_file}")
        return

    # Load query scores
    print(f"加载查询评分数据: {args.input_file}")
    query_scores = load_query_scores(args.input_file)
    print(f"共加载 {len(query_scores)} 个查询")

    # Convert to JSONL format
    print(f"筛选评分 >= {args.score_threshold} 的查询...")
    converted_queries = convert_to_jsonl_format(query_scores, args.score_threshold)
    print(f"筛选出 {len(converted_queries)} 个高价值查询")

    # Get queries for statistics (same as filtered_queries in convert function)
    if args.score_threshold > 0:
        stats_queries = [
            q for q in query_scores
            if "overall_score" in q["scoring_result"] and
               q["scoring_result"]["overall_score"] >= args.score_threshold
        ]
    else:
        stats_queries = [
            q for q in query_scores
            if "overall_score" in q["scoring_result"]
        ]
    stats_queries.sort(
        key=lambda x: x["scoring_result"]["overall_score"],
        reverse=True
    )

    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    # Backup original file if requested
    if args.backup_original and args.output_file == "data/prompt_data/query.jsonl":
        original_file = "data/prompt_data/query.jsonl"
        if os.path.exists(original_file):
            backup_file = "data/prompt_data/query_original_backup.jsonl"
            os.rename(original_file, backup_file)
            print(f"原文件已备份为: {backup_file}")

    # Save converted queries
    save_as_jsonl(converted_queries, args.output_file)

    # Print statistics
    print("\n=== 转换统计 ===")
    print(f"原始查询数量: {len(query_scores)}")
    print(f"筛选后数量: {len(converted_queries)}")
    print(f"筛选比例: {len(converted_queries)/len(query_scores)*100:.1f}%")

    if converted_queries:
        # Get scores from original data for statistics
        original_scores = [q["scoring_result"]["overall_score"] for q in stats_queries]
        print(f"得分范围: {min(original_scores):.2f} - {max(original_scores):.2f}")
        print(f"平均得分: {sum(original_scores)/len(original_scores):.2f}")

    # Show topic distribution
    topic_counts = {}
    for query in converted_queries:
        topic = query["topic"]
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    print(f"\n=== 主题分布 ===")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{topic}: {count} ({count/len(converted_queries)*100:.1f}%)")

    # Show top queries
    print(f"\n=== 前5个最高分查询 ===")
    for i, (original_query, converted_query) in enumerate(zip(stats_queries[:5], converted_queries[:5]), 1):
        score = original_query["scoring_result"]["overall_score"]
        title = original_query["query_title"]
        print(f"{i}. [{score:.2f}分] {title}")

if __name__ == "__main__":
    main()