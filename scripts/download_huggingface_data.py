#!/usr/bin/env python3
"""
从 HuggingFace 下载 LifelongAgentBench 数据集并转换为项目需要的格式
"""
import argparse
import json
import os
import sys
import glob
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Error: datasets library not installed.")
    print("Please install it with: pip install datasets")
    sys.exit(1)


def download_and_convert_db_bench(
    output_dir: str = "./data/v0303/db_bench/processed/huggingface",
    split: str = "train",
    dataset_name: str = "csyq/LifelongAgentBench",
):
    """
    从 HuggingFace 下载 DB bench 数据集并转换为 entry_dict.json 格式
    
    Args:
        output_dir: 输出目录
        split: 数据集分割（train/validation/test）
        dataset_name: HuggingFace 数据集名称
    """
    print(f"Downloading dataset: {dataset_name}")
    print(f"Split: {split}")
    print(f"Output directory: {output_dir}")
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # 加载数据集 - 指定 data_dir 只加载 db_bench 子数据集
        print("\nLoading dataset from HuggingFace...")
        print("Note: Loading db_bench subset only (to avoid schema conflicts)...")
        try:
            # 方法1: 使用 data_dir 参数只加载 db_bench
            dataset = load_dataset(
                dataset_name, 
                split=split,
                data_dir="db_bench"
            )
        except Exception as e1:
            # 方法2: 如果 data_dir 不支持，尝试直接指定路径
            print(f"data_dir approach failed: {e1}")
            print("Trying alternative approach: loading from parquet files directly...")
            try:
                # 直接加载 parquet 文件
                dataset = load_dataset(
                    "parquet",
                    data_files=f"{dataset_name}/db_bench/train-*.parquet",
                    split=split
                )
            except Exception as e2:
                # 方法3: 使用本地已下载的文件
                print(f"Parquet approach failed: {e2}")
                print("Trying to use local cached files...")
                local_path = os.path.expanduser("~/.cache/huggingface/hub/datasets--csyq--LifelongAgentBench")
                # 查找所有快照目录
                snapshots = glob.glob(f"{local_path}/snapshots/*")
                if snapshots:
                    latest_snapshot = max(snapshots, key=os.path.getmtime)
                    parquet_files = glob.glob(f"{latest_snapshot}/db_bench/train-*.parquet")
                    if parquet_files:
                        print(f"Found {len(parquet_files)} parquet file(s) in {latest_snapshot}")
                        dataset = load_dataset("parquet", data_files=parquet_files, split=split)
                    else:
                        raise FileNotFoundError(f"No parquet files found in {latest_snapshot}/db_bench/")
                else:
                    raise FileNotFoundError(f"No snapshots found in {local_path}")
        
        print(f"Dataset loaded. Total samples: {len(dataset)}")
        
        # 检查第一个样本的字段结构
        if len(dataset) > 0:
            print("\nSample fields:", list(dataset[0].keys()))
            print("First sample preview:")
            first_sample = dataset[0]
            for key, value in first_sample.items():
                if isinstance(value, (str, int, float, list)):
                    preview = str(value)[:100] if isinstance(value, str) else value
                    print(f"  {key}: {preview}")
        
        # 转换为 entry_dict 格式
        print("\nConverting to entry_dict format...")
        entry_dict = {}
        
        for idx, sample in enumerate(dataset):
            # 处理字段映射 - HuggingFace 数据集可能使用不同的字段名
            # answer_info 可能是字符串（JSON）或字典
            answer_info = sample.get("answer_info")
            if isinstance(answer_info, str):
                import json
                try:
                    answer_info = json.loads(answer_info)
                except:
                    answer_info = {}
            elif answer_info is None:
                answer_info = {}
            
            # table_info 可能是字符串（JSON）或字典
            table_info = sample.get("table_info")
            if isinstance(table_info, str):
                import json
                try:
                    table_info = json.loads(table_info)
                except:
                    table_info = {}
            elif table_info is None:
                table_info = {}
            
            # skill_list 可能是字符串（JSON）或列表
            skill_list = sample.get("skill_list")
            if isinstance(skill_list, str):
                import json
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
        output_file = output_path / "entry_dict.json"
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
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Ensure you have access to HuggingFace datasets")
        print("3. Try installing/updating: pip install datasets")
        print("4. If using a proxy, configure it properly")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Download LifelongAgentBench dataset from HuggingFace"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./data/v0303/db_bench/processed/huggingface",
        help="Output directory for converted data",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "validation", "test"],
        help="Dataset split to download",
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="csyq/LifelongAgentBench",
        help="HuggingFace dataset name",
    )
    
    args = parser.parse_args()
    
    download_and_convert_db_bench(
        output_dir=args.output_dir,
        split=args.split,
        dataset_name=args.dataset_name,
    )


if __name__ == "__main__":
    main()

