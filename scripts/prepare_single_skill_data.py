#!/usr/bin/env python3
"""
准备single-skill tasks数据的脚本。

从现有的DB benchmark数据中提取single-skill tasks，并保存为JSON格式。
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
script_dir = Path(__file__).parent
project_root = script_dir.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def load_and_filter_single_skill_tasks(
    input_data_path: str, min_tasks_per_skill: int = 1
) -> dict:
    """
    从输入数据中加载并筛选single-skill tasks。
    
    Args:
        input_data_path: 输入数据文件路径
        min_tasks_per_skill: 每个skill最少需要的task数量
    
    Returns:
        按skill组织的task字典
    """
    # 加载数据
    with open(input_data_path, "r") as f:
        data = json.load(f)
    
    # 按skill组织tasks
    skill_to_tasks: dict[str, list] = {}
    
    for key, entry in data.items():
        skill_list = entry.get("skill_list", [])
        # 只包含single-skill tasks
        if len(skill_list) == 1:
            skill = skill_list[0]
            if skill not in skill_to_tasks:
                skill_to_tasks[skill] = []
            skill_to_tasks[skill].append(entry)
    
    # 过滤skills
    filtered_skill_to_tasks = {
        skill: tasks
        for skill, tasks in skill_to_tasks.items()
        if len(tasks) >= min_tasks_per_skill
    }
    
    return filtered_skill_to_tasks


def main():
    parser = argparse.ArgumentParser(
        description="Prepare single-skill tasks from existing DB benchmark data"
    )
    parser.add_argument(
        "--input_data_path",
        type=str,
        required=True,
        help="Path to input DB benchmark data JSON file",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Path to output single-skill tasks JSON file",
    )
    parser.add_argument(
        "--min_tasks_per_skill",
        type=int,
        default=1,
        help="Minimum number of tasks per skill to include (default: 1)",
    )

    args = parser.parse_args()

    # Load and filter single-skill tasks
    print(f"Loading data from {args.input_data_path}...")
    skill_to_tasks = load_and_filter_single_skill_tasks(
        args.input_data_path, args.min_tasks_per_skill
    )

    # Print statistics
    available_skills = list(skill_to_tasks.keys())
    print(f"Found {len(available_skills)} skills with single-skill tasks:")
    for skill in sorted(available_skills):
        task_count = len(skill_to_tasks[skill])
        print(f"  - {skill}: {task_count} tasks")

    print(
        f"\nAfter filtering (min_tasks_per_skill={args.min_tasks_per_skill}): "
        f"{len(available_skills)} skills"
    )

    # Save to JSON
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving single-skill tasks to {args.output_path}...")
    with open(args.output_path, "w") as f:
        json.dump(skill_to_tasks, f, indent=2)

    # Print final statistics
    total_tasks = sum(len(tasks) for tasks in skill_to_tasks.values())
    print(f"\nStatistics:")
    print(f"  Total skills: {len(available_skills)}")
    print(f"  Total tasks: {total_tasks}")
    if len(available_skills) > 0:
        print(f"  Average tasks per skill: {total_tasks / len(available_skills):.2f}")

    print(f"\n✓ Successfully saved single-skill tasks to {args.output_path}")


if __name__ == "__main__":
    main()

