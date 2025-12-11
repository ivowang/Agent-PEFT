#!/usr/bin/env python3
"""
从本地已下载的 parquet 文件转换数据
"""
import argparse
import json
import os
import sys
import glob
from pathlib import Path

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError:
    print("Error: Required libraries not installed.")
    print("Please install: pip install datasets pandas pyarrow")
    sys.exit(1)


def convert_parquet_to_entry_dict(
    parquet_path: str,
    output_path: str,
):
    """
    从 parquet 文件转换为 entry_dict.json 格式
    
    Args:
        parquet_path: parquet 文件路径（支持通配符）
        output_path: 输出 JSON 文件路径
    """
    print(f"Loading parquet file(s): {parquet_path}")
    
    # 查找所有匹配的 parquet 文件
    parquet_files = glob.glob(parquet_path)
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found matching: {parquet_path}")
    
    print(f"Found {len(parquet_files)} parquet file(s)")
    
    # 加载数据集
    dataset = load_dataset("parquet", data_files=parquet_files, split="train")
    print(f"Dataset loaded. Total samples: {len(dataset)}")
    
    # 检查第一个样本的字段结构
    if len(dataset) > 0:
        print("\nSample fields:", list(dataset[0].keys()))
        print("First sample preview:")
        first_sample = dataset[0]
        for key, value in first_sample.items():
            if isinstance(value, (str, int, float)):
                preview = str(value)[:100] if isinstance(value, str) else value
                print(f"  {key}: {preview}")
            elif isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
            elif isinstance(value, dict):
                print(f"  {key}: dict with keys {list(value.keys())}")
    
    # 转换为 entry_dict 格式
    print("\nConverting to entry_dict format...")
    entry_dict = {}
    
    for idx, sample in enumerate(dataset):
        # 处理字段映射
        # answer_info 可能是字符串（JSON）或字典
        answer_info = sample.get("answer_info")
        if isinstance(answer_info, str):
            try:
                answer_info = json.loads(answer_info)
            except:
                answer_info = {}
        elif answer_info is None:
            answer_info = {}
        
        # table_info 可能是字符串（JSON）或字典
        table_info = sample.get("table_info")
        if isinstance(table_info, str):
            try:
                table_info = json.loads(table_info)
            except:
                table_info = {}
        elif table_info is None:
            table_info = {}
        
        # skill_list 可能是字符串（JSON）或列表
        skill_list = sample.get("skill_list")
        if isinstance(skill_list, str):
            try:
                skill_list = json.loads(skill_list)
            except:
                skill_list = []
        elif skill_list is None:
            skill_list = []
        
        # 构建 entry
        entry = {
            "answer_info": {
                "direct": answer_info.get("direct") if isinstance(answer_info, dict) else sample.get("answer_direct"),
                "md5": answer_info.get("md5") if isinstance(answer_info, dict) else sample.get("answer_md5"),
                "sql": answer_info.get("sql") if isinstance(answer_info, dict) else sample.get("sql"),
            },
            "table_info": {
                "name": table_info.get("name") if isinstance(table_info, dict) else sample.get("table_name"),
                "column_info_list": table_info.get("column_info_list", []) if isinstance(table_info, dict) else sample.get("column_info_list", []),
                "row_list": table_info.get("row_list", []) if isinstance(table_info, dict) else sample.get("row_list", []),
            },
            "instruction": sample.get("instruction"),
            "skill_list": skill_list if isinstance(skill_list, list) else [],
        }
        
        entry_dict[str(idx)] = entry
        
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(dataset)} samples...")
    
    # 保存为 JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, "w") as f:
        json.dump(entry_dict, f, indent=2)
    
    print(f"\n✓ Successfully converted {len(entry_dict)} samples")
    print(f"✓ Saved to: {output_file}")
    
    # 打印统计信息
    print("\nStatistics:")
    print(f"  Total samples: {len(entry_dict)}")
    if entry_dict:
        first_entry = entry_dict["0"]
        skills = first_entry.get("skill_list", [])
        print(f"  Sample skills: {skills}")
    
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(
        description="Convert local parquet files to entry_dict.json format"
    )
    parser.add_argument(
        "--parquet_path",
        type=str,
        default="./data/LifelongAgentBench/db_bench/train-*.parquet",
        help="Path to parquet file(s) (supports wildcards)",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="./data/v0303/db_bench/processed/huggingface/entry_dict.json",
        help="Output JSON file path",
    )
    
    args = parser.parse_args()
    
    convert_parquet_to_entry_dict(
        parquet_path=args.parquet_path,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()

