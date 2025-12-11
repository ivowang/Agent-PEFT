#!/usr/bin/env python3
"""
准备single-skill tasks数据的脚本。

从现有的DB benchmark数据中提取single-skill tasks，并保存为JSON格式。
"""

import argparse
import json
import os
from pathlib import Path
from src.tasks.instance.db_bench.single_skill_task_generator import (
    SingleSkillTaskGenerator,
)


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

    # Load generator from existing data
    print(f"Loading data from {args.input_data_path}...")
    generator = SingleSkillTaskGenerator.load_from_existing_data(
        args.input_data_path
    )

    # Get available skills
    available_skills = generator.get_available_skills()
    print(f"Found {len(available_skills)} skills with single-skill tasks:")
    for skill in available_skills:
        task_count = len(generator.skill_to_tasks[skill])
        print(f"  - {skill}: {task_count} tasks")

    # Filter skills by minimum task count
    filtered_skills = [
        skill
        for skill in available_skills
        if len(generator.skill_to_tasks[skill]) >= args.min_tasks_per_skill
    ]
    print(
        f"\nAfter filtering (min_tasks_per_skill={args.min_tasks_per_skill}): "
        f"{len(filtered_skills)} skills"
    )

    # Create filtered skill_to_tasks dict
    filtered_skill_to_tasks = {
        skill: generator.skill_to_tasks[skill] for skill in filtered_skills
    }

    # Save to JSON
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving single-skill tasks to {args.output_path}...")
    with open(args.output_path, "w") as f:
        json.dump(filtered_skill_to_tasks, f, indent=2)

    # Print statistics
    total_tasks = sum(len(tasks) for tasks in filtered_skill_to_tasks.values())
    print(f"\nStatistics:")
    print(f"  Total skills: {len(filtered_skills)}")
    print(f"  Total tasks: {total_tasks}")
    print(f"  Average tasks per skill: {total_tasks / len(filtered_skills):.2f}")

    print(f"\n✓ Successfully saved single-skill tasks to {args.output_path}")


if __name__ == "__main__":
    main()

