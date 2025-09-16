import pandas as pd
import json
import time
from openai import OpenAI
from prompt.criteria_prompt_zh import (
    generate_eval_dimension_weight_prompt,
    generate_eval_criteria_prompt_comp,
    generate_eval_criteria_prompt_insight,
    generate_eval_criteria_prompt_Inst,
    generate_eval_criteria_prompt_readability
)
import os
from dotenv import load_dotenv
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1'),
    api_key=os.getenv('OPENAI_API_KEY'),
)

def extract_json_from_response(response_text):
    """从响应文本中提取JSON内容"""
    try:
        # 查找json_output标签
        start_tag = "<json_output>"
        end_tag = "</json_output>"
        
        start_idx = response_text.find(start_tag)
        end_idx = response_text.find(end_tag)
        
        if start_idx != -1 and end_idx != -1:
            json_content = response_text[start_idx + len(start_tag):end_idx].strip()
            # 解析JSON
            return json.loads(json_content)
        else:
            # 如果没有找到标签，尝试直接解析整个响应
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"响应内容: {response_text}")
        return None

def generate_dimension_weights(task_prompt, standard_answer):
    """生成四个维度的权重"""
    prompt = generate_eval_dimension_weight_prompt.format(
        task_prompt=task_prompt,
        standard_answer=standard_answer
    )
    
    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.5-pro",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        weights = extract_json_from_response(response)
        return weights
    except Exception as e:
        print(f"生成维度权重时出错: {e}")
        return None

def generate_criteria_for_dimension(task_prompt, standard_answer, dimension_prompt, dimension_name):
    """为指定维度生成评判标准"""
    prompt = dimension_prompt.format(
        task_prompt=task_prompt,
        standard_answer=standard_answer
    )
    
    try:
        completion = client.chat.completions.create(
            model="google/gemini-2.5-pro",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        criteria = extract_json_from_response(response)
        return criteria
    except Exception as e:
        print(f"生成{dimension_name}评判标准时出错: {e}")
        return None

def generate_complete_rubric(task_prompt, standard_answer):
    """生成完整的rubric"""
    print(f"正在为任务生成rubric: {task_prompt[:50]}...")
    
    # 1. 生成四个维度的权重
    print("  生成维度权重...")
    weights = generate_dimension_weights(task_prompt, standard_answer)
    if not weights:
        return None
    
    # 2. 为每个维度生成具体的评判标准
    rubric = {
        "task": task_prompt,
        "dimension_weights": weights,
        "criteria": {}
    }
    
    # 全面性
    print("  生成全面性评判标准...")
    rubric["criteria"]["comprehensiveness"] = generate_criteria_for_dimension(
        task_prompt, standard_answer, 
        generate_eval_criteria_prompt_comp, "全面性"
    )
    
    # 洞察力
    print("  生成洞察力评判标准...")
    rubric["criteria"]["insight"] = generate_criteria_for_dimension(
        task_prompt, standard_answer, 
        generate_eval_criteria_prompt_insight, "洞察力"
    )
    
    # 指令遵循能力
    print("  生成指令遵循能力评判标准...")
    rubric["criteria"]["instruction_following"] = generate_criteria_for_dimension(
        task_prompt, standard_answer, 
        generate_eval_criteria_prompt_Inst, "指令遵循能力"
    )
    
    # 可读性
    print("  生成可读性评判标准...")
    rubric["criteria"]["readability"] = generate_criteria_for_dimension(
        task_prompt, standard_answer, 
        generate_eval_criteria_prompt_readability, "可读性"
    )
    
    return rubric

def main():
    # 读取CSV数据
    df = pd.read_csv('deep_research_data.csv')
    
    all_rubrics = []
    
    for index, row in df.iterrows():
        print(f"\n处理第 {index + 1} 条数据...")
        print(f"行业: {row['所属行业']}")
        print(f"问题: {row['问题名称'][:50]}...")
        
        task_prompt = row['问题名称']
        standard_answer = row['参考答案']
        
        # 生成rubric
        rubric = generate_complete_rubric(task_prompt, standard_answer)
        
        if rubric:
            rubric["industry"] = row['所属行业']
            rubric["question_name"] = row['问题名称']
            all_rubrics.append(rubric)
            print(f"  ✓ 成功生成rubric")
        else:
            print(f"  ✗ 生成rubric失败")
        
        # 添加延迟避免API限制
        time.sleep(2)
    
    # 保存所有rubric到JSON文件
    with open('generated_rubrics.json', 'w', encoding='utf-8') as f:
        json.dump(all_rubrics, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！共生成 {len(all_rubrics)} 个rubric，已保存到 generated_rubrics.json")

if __name__ == "__main__":
    main() 