#!/usr/bin/env python3

"""
Convert query_rubrics.json to criteria.jsonl format for POET evaluation.
"""

import json
import os

def convert_rubrics_to_criteria(rubrics_file, query_file, output_file):
    """
    Convert rubrics JSON to criteria JSONL format
    """
    # Load rubrics data
    with open(rubrics_file, 'r', encoding='utf-8') as f:
        rubrics_data = json.load(f)

    # Load query data to get prompts and IDs
    query_data = {}
    with open(query_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                query_item = json.loads(line)
                query_data[query_item['id']] = query_item

    # Create mapping from rubrics to query data
    converted_criteria = []

    for rubric in rubrics_data:
        query_number = rubric.get('query_number')
        query_content = rubric.get('query_content', '')

        # Find matching query in query.jsonl by content or number
        matching_query = None
        for qid, qdata in query_data.items():
            # Try to match by query content similarity or by query number
            if (query_content in qdata.get('prompt', '') or
                qdata.get('prompt', '') in query_content or
                qid == query_number):
                matching_query = qdata
                break

        if matching_query:
            # Convert rubric format to criteria format
            criteria_item = {
                "id": matching_query['id'],
                "prompt": matching_query['prompt'],
                "dimension_weight": rubric.get('dimension_weights', {
                    "comprehensiveness": 0.3,
                    "insight": 0.36,
                    "instruction_following": 0.2,
                    "readability": 0.14
                }),
                "criterions": {}
            }

            # Convert criteria for each dimension
            rubric_criteria = rubric.get('criteria', {})
            for dimension in ['comprehensiveness', 'insight', 'instruction_following', 'readability']:
                if dimension in rubric_criteria:
                    criteria_item["criterions"][dimension] = rubric_criteria[dimension]
                else:
                    # Provide default criteria if missing
                    criteria_item["criterions"][dimension] = [
                        {
                            "criterion": f"Default {dimension} criterion",
                            "explanation": f"Default explanation for {dimension}",
                            "weight": 1.0
                        }
                    ]

            converted_criteria.append(criteria_item)
        else:
            print(f"Warning: Could not find matching query for rubric {query_number}: {query_content[:100]}...")

    # If no matches found, create criteria for all queries with default values
    if not converted_criteria:
        print("No rubric matches found, creating default criteria for all queries...")
        for qid, qdata in query_data.items():
            criteria_item = {
                "id": qid,
                "prompt": qdata['prompt'],
                "dimension_weight": {
                    "comprehensiveness": 0.3,
                    "insight": 0.36,
                    "instruction_following": 0.2,
                    "readability": 0.14
                },
                "criterions": {
                    dimension: [
                        {
                            "criterion": f"Default {dimension} criterion",
                            "explanation": f"Default explanation for {dimension}",
                            "weight": 1.0
                        }
                    ] for dimension in ['comprehensiveness', 'insight', 'instruction_following', 'readability']
                }
            }
            converted_criteria.append(criteria_item)

    # Sort by ID
    converted_criteria.sort(key=lambda x: x['id'])

    # Write to JSONL format
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in converted_criteria:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Converted {len(converted_criteria)} criteria items to {output_file}")
    return converted_criteria

if __name__ == "__main__":
    rubrics_file = "query_rubrics.json"
    query_file = "data/prompt_data/query.jsonl"
    output_file = "data/criteria_data/criteria.jsonl"

    converted_criteria = convert_rubrics_to_criteria(rubrics_file, query_file, output_file)

    print("\nSample converted criteria:")
    if converted_criteria:
        sample = converted_criteria[0]
        print(f"ID: {sample['id']}")
        print(f"Prompt: {sample['prompt'][:100]}...")
        print(f"Weights: {sample['dimension_weight']}")
        print(f"Comprehensiveness criteria count: {len(sample['criterions']['comprehensiveness'])}")