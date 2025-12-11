#!/usr/bin/env python3
"""
创建最小测试数据集，用于快速测试RL训练功能。

这个脚本会创建一个包含少量single-skill tasks的测试数据集。
"""

import argparse
import json
import os
from pathlib import Path


def create_minimal_test_data(output_path: str, num_samples: int = 10):
    """
    创建最小测试数据集。
    
    Args:
        output_path: 输出文件路径
        num_samples: 样本数量
    """
    # 定义一些简单的single-skill tasks
    test_tasks = {
        "0": {
            "answer_info": {
                "direct": [["Alice", 25], ["Bob", 30]],
                "md5": None,
                "sql": "SELECT name, age FROM users WHERE age > 20"
            },
            "table_info": {
                "name": "users",
                "column_info_list": [
                    {"name": "name", "type": "VARCHAR(50)"},
                    {"name": "age", "type": "INT"}
                ],
                "row_list": [
                    ["Alice", 25],
                    ["Bob", 30],
                    ["Charlie", 18]
                ]
            },
            "instruction": "Find all users older than 20 years old.",
            "skill_list": ["select"]
        },
        "1": {
            "answer_info": {
                "direct": [["Alice", 25]],
                "md5": None,
                "sql": "SELECT name, age FROM users WHERE age = 25"
            },
            "table_info": {
                "name": "users",
                "column_info_list": [
                    {"name": "name", "type": "VARCHAR(50)"},
                    {"name": "age", "type": "INT"}
                ],
                "row_list": [
                    ["Alice", 25],
                    ["Bob", 30],
                    ["Charlie", 18]
                ]
            },
            "instruction": "Find users who are exactly 25 years old.",
            "skill_list": ["where_single_condition"]
        },
        "2": {
            "answer_info": {
                "direct": [["Alice", 25], ["Bob", 30]],
                "md5": None,
                "sql": "SELECT name, age FROM users ORDER BY age ASC"
            },
            "table_info": {
                "name": "users",
                "column_info_list": [
                    {"name": "name", "type": "VARCHAR(50)"},
                    {"name": "age", "type": "INT"}
                ],
                "row_list": [
                    ["Alice", 25],
                    ["Bob", 30],
                    ["Charlie", 18]
                ]
            },
            "instruction": "List all users sorted by age in ascending order.",
            "skill_list": ["order_by_single_column"]
        },
        "3": {
            "answer_info": {
                "direct": [["Alice", 25]],
                "md5": None,
                "sql": "SELECT name, age FROM users LIMIT 1"
            },
            "table_info": {
                "name": "users",
                "column_info_list": [
                    {"name": "name", "type": "VARCHAR(50)"},
                    {"name": "age", "type": "INT"}
                ],
                "row_list": [
                    ["Alice", 25],
                    ["Bob", 30],
                    ["Charlie", 18]
                ]
            },
            "instruction": "Get the first user from the users table.",
            "skill_list": ["limit_only"]
        },
        "4": {
            "answer_info": {
                "direct": None,
                "md5": "abc123def456",
                "sql": "INSERT INTO users (name, age) VALUES ('David', 28)"
            },
            "table_info": {
                "name": "users",
                "column_info_list": [
                    {"name": "name", "type": "VARCHAR(50)"},
                    {"name": "age", "type": "INT"}
                ],
                "row_list": [
                    ["Alice", 25],
                    ["Bob", 30]
                ]
            },
            "instruction": "Insert a new user named David who is 28 years old.",
            "skill_list": ["insert"]
        }
    }
    
    # 如果请求的样本数少于已有任务，只取前N个
    if num_samples <= len(test_tasks):
        selected_tasks = {str(i): test_tasks[str(i)] for i in range(num_samples)}
    else:
        # 如果请求更多样本，循环使用现有任务
        selected_tasks = {}
        for i in range(num_samples):
            task_idx = str(i % len(test_tasks))
            selected_tasks[str(i)] = test_tasks[task_idx].copy()
    
    # 创建输出目录
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存数据
    with open(output_path, "w") as f:
        json.dump(selected_tasks, f, indent=2)
    
    print(f"✓ Created minimal test data with {len(selected_tasks)} samples")
    print(f"  Output: {output_path}")
    print(f"  Skills included: {set([task['skill_list'][0] for task in selected_tasks.values()])}")


def main():
    parser = argparse.ArgumentParser(
        description="Create minimal test data for RL training"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="./data/v0303/db_bench/processed/v0317_first500/entry_dict.json",
        help="Output path for the test data file",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=10,
        help="Number of samples to generate (default: 10)",
    )
    
    args = parser.parse_args()
    
    create_minimal_test_data(args.output_path, args.num_samples)


if __name__ == "__main__":
    main()

