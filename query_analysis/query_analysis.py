#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询评分分析程序
从query_scores.json文件中提取overall_score前5和后5的查询，
并将结果输出到markdown文件
"""

import json
import os
from typing import List, Dict, Any

def load_query_scores(file_path: str) -> List[Dict[str, Any]]:
    """加载查询评分数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def sort_queries_by_score(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按overall_score降序排序"""
    return sorted(queries, key=lambda x: x['scoring_result']['overall_score'], reverse=True)

def format_score_reason(score_data: Dict[str, Any]) -> str:
    """格式化评分原因"""
    return f"**评分：{score_data['score']}分**\n\n{score_data['reason']}"

def format_query_to_markdown(query: Dict[str, Any], rank: int) -> str:
    """将单个查询格式化为markdown"""
    scoring_result = query['scoring_result']
    overall_score = scoring_result['overall_score']
    
    markdown = f"""## {rank}. {query['query_title']} (查询编号: {query['query_number']})

**总体评分：{overall_score}分**

### 查询内容
{query['query_content']}

### 各项评分详情

"""
    
    # 添加各项评分
    for criterion, score_data in scoring_result['scores'].items():
        markdown += f"#### {criterion}\n"
        markdown += format_score_reason(score_data) + "\n\n"
    
    return markdown

def generate_markdown_report(queries: List[Dict[str, Any]], output_file: str):
    """生成markdown报告"""
    sorted_queries = sort_queries_by_score(queries)
    
    # 获取前5和后5
    top_5 = sorted_queries[:5]
    bottom_5 = sorted_queries[-5:]
    
    markdown_content = """# 查询评分分析报告

本报告展示了查询评分中overall_score最高的前5个查询和最低的后5个查询。

## 评分标准说明

- **A. 决策颠覆性**: 答案对决策的影响程度
- **B. 分析复杂性**: 解决问题的认知复杂度
- **C. 行动导向性**: 答案的可执行性
- **D. 风险/收益规模**: 问题关联的风险和收益规模
- **E. 时效敏感性**: 对信息时效性的要求
- **F. 专业壁垒**: 所需专业知识的稀缺程度
- **G. 可验证性**: 答案的可验证程度

---

# 前5名查询（overall_score最高）

"""
    
    # 添加前5名
    for i, query in enumerate(top_5, 1):
        markdown_content += format_query_to_markdown(query, i)
        markdown_content += "---\n\n"
    
    markdown_content += """# 后5名查询（overall_score最低）

"""
    
    # 添加后5名
    for i, query in enumerate(bottom_5, 1):
        markdown_content += format_query_to_markdown(query, i)
        markdown_content += "---\n\n"
    
    # 添加统计信息
    all_scores = [q['scoring_result']['overall_score'] for q in sorted_queries]
    markdown_content += f"""# 统计信息

- **总查询数量**: {len(queries)}
- **最高分**: {max(all_scores):.2f}
- **最低分**: {min(all_scores):.2f}
- **平均分**: {sum(all_scores)/len(all_scores):.2f}
- **中位数**: {sorted(all_scores)[len(all_scores)//2]:.2f}

## 前5名查询概览

| 排名 | 查询编号 | 查询标题 | 总体评分 |
|------|----------|----------|----------|
"""
    
    for i, query in enumerate(top_5, 1):
        markdown_content += f"| {i} | {query['query_number']} | {query['query_title']} | {query['scoring_result']['overall_score']:.2f} |\n"
    
    markdown_content += """
## 后5名查询概览

| 排名 | 查询编号 | 查询标题 | 总体评分 |
|------|----------|----------|----------|
"""
    
    for i, query in enumerate(bottom_5, 1):
        markdown_content += f"| {i} | {query['query_number']} | {query['query_title']} | {query['scoring_result']['overall_score']:.2f} |\n"
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"报告已生成：{output_file}")

def main():
    """主函数"""
    input_file = "query_scores.json"
    output_file = "query_analysis_report.md"
    
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 {input_file}")
        return
    
    try:
        # 加载数据
        queries = load_query_scores(input_file)
        print(f"成功加载 {len(queries)} 个查询")
        
        # 生成报告
        generate_markdown_report(queries, output_file)
        
        # 显示简要统计
        sorted_queries = sort_queries_by_score(queries)
        print(f"\n简要统计：")
        print(f"最高分：{sorted_queries[0]['scoring_result']['overall_score']:.2f} - {sorted_queries[0]['query_title']}")
        print(f"最低分：{sorted_queries[-1]['scoring_result']['overall_score']:.2f} - {sorted_queries[-1]['query_title']}")
        
    except Exception as e:
        print(f"处理过程中出现错误：{e}")

if __name__ == "__main__":
    main()
