#!/usr/bin/env python3
"""
Convert MD files to JSONL format for benchmark evaluation.
Extracts metrics from raw model outputs and formats them for scoring.
"""

import json
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


def extract_metrics_from_content(content: str) -> Dict[str, int]:
    """
    Extract metrics from content: sources_used, citation_count, word_count

    Args:
        content: Raw article content

    Returns:
        Dictionary with extracted metrics
    """
    # Count citations by looking for [number] patterns
    citation_pattern = r'\[(\d+)\]'
    citations = re.findall(citation_pattern, content)
    citation_count = len(citations)

    # Count unique sources (unique citation numbers)
    unique_citations = set(int(c) for c in citations)
    sources_used = len(unique_citations)

    # Count words (Chinese text needs special handling)
    # Remove line numbers and tabs first
    clean_content = re.sub(r'^\s*\d+→', '', content, flags=re.MULTILINE)

    # Count Chinese characters as words, and split English words by spaces
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_content))
    english_words = len(re.findall(r'[a-zA-Z]+', clean_content))

    # For mixed content, count Chinese chars + English words
    word_count = chinese_chars + english_words

    return {
        "sources_used": sources_used,
        "citation_count": citation_count,
        "word_count": word_count
    }


def extract_query_from_file(query_file: str, query_id: int) -> str:
    """
    Extract the original query prompt from query.jsonl file

    Args:
        query_file: Path to query.jsonl file
        query_id: ID of the query to extract

    Returns:
        The prompt text for the given ID
    """
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                if data.get('id') == query_id:
                    return data.get('prompt', '')
    except Exception as e:
        print(f"Warning: Could not extract query {query_id} from {query_file}: {e}")

    return f"Query {query_id}"  # Fallback


def parse_md_filename(filename: str) -> Tuple[int, str]:
    """
    Parse MD filename to extract ID and model name
    Examples: "1-GPT.md" -> (1, "GPT"), "2-Claude.md" -> (2, "Claude")

    Args:
        filename: MD filename

    Returns:
        Tuple of (id, model_name)
    """
    basename = os.path.splitext(filename)[0]  # Remove .md extension

    # Match pattern like "1-GPT" or "2-Claude"
    match = re.match(r'^(\d+)-(.+)$', basename)
    if match:
        return int(match.group(1)), match.group(2)

    # Fallback: try to extract number from start
    match = re.match(r'^(\d+)', basename)
    if match:
        return int(match.group(1)), basename

    raise ValueError(f"Cannot parse filename: {filename}")


def convert_md_to_jsonl_entry(md_file: str, query_file: str = None) -> Dict:
    """
    Convert a single MD file to JSONL entry format

    Args:
        md_file: Path to MD file
        query_file: Path to query.jsonl file (optional)

    Returns:
        Dictionary in required JSONL format
    """
    # Parse filename to get ID and model info
    filename = os.path.basename(md_file)
    query_id, model_name = parse_md_filename(filename)

    # Read content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract original query if query_file provided
    if query_file and os.path.exists(query_file):
        prompt = extract_query_from_file(query_file, query_id)
    else:
        prompt = f"Query {query_id}"

    # Extract metrics
    metrics = extract_metrics_from_content(content)

    # Build execution_metrics (some values are estimated/placeholder)
    execution_metrics = {
        "total_duration_seconds": 1200,  # Placeholder
        "token_usage": {
            "input_tokens": 2500,  # Placeholder
            "output_tokens": metrics["word_count"] * 2,  # Rough estimate
            "total_cost_usd": 0.087  # Placeholder
        },
        "automation_level": 0.95,  # Placeholder
        "tool_calls_count": 8,  # Placeholder
        "sources_used": metrics["sources_used"],
        "citation_count": metrics["citation_count"],
        "word_count": metrics["word_count"]
    }

    return {
        "id": query_id,
        "prompt": prompt,
        "article": content,
        "execution_metrics": execution_metrics
    }


def convert_directory(input_dir: str, output_file: str, query_file: str = None):
    """
    Convert all MD files in directory to a single JSONL file

    Args:
        input_dir: Directory containing MD files
        output_file: Output JSONL file path
        query_file: Path to query.jsonl file (optional)
    """
    input_path = Path(input_dir)
    md_files = list(input_path.glob("*.md"))

    if not md_files:
        print(f"No MD files found in {input_dir}")
        return

    print(f"Found {len(md_files)} MD files in {input_dir}")

    entries = []
    for md_file in sorted(md_files):
        try:
            entry = convert_md_to_jsonl_entry(str(md_file), query_file)
            entries.append(entry)
            print(f"Converted: {md_file.name} -> ID {entry['id']}")
        except Exception as e:
            print(f"Error converting {md_file.name}: {e}")

    # Sort by ID
    entries.sort(key=lambda x: x['id'])
    print(output_file)
    # Write JSONL
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"Converted {len(entries)} entries to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Convert MD files to JSONL format")
    parser.add_argument("input_dir", help="Directory containing MD files")
    parser.add_argument("output_file", help="Output JSONL file path")
    parser.add_argument("--query_file", help="Path to query.jsonl file for extracting prompts")

    args = parser.parse_args()

    convert_directory(args.input_dir, args.output_file, args.query_file)


if __name__ == "__main__":
    main()