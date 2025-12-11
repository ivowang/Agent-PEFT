#!/usr/bin/env python3
"""
完整的DB bench数据生成脚本
生成包含instruction, ground truth SQL, skill list的单技能训练数据
"""
import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.tasks.instance.db_bench.task import (
    DBBenchSkillUtility, 
    DBBenchContainer,
    DBBenchDatasetItem, 
    AnswerInfo, 
    AnswerType, 
    TableInfo, 
    ColumnInfo,
    DBBench
)


class DBBenchDataGenerator:
    """DB bench数据生成器"""
    
    # 所有可用的技能
    ALL_SKILLS = [
        "select",
        "insert",
        "delete",
        "update",
        "where_single_condition",
        "where_multiple_conditions",
        "order_by_single_column",
        "limit_only",
        "column_alias",
        "table_alias",
        "where_nested_conditions",
        "group_by_single_column",
        "group_by_multiple_columns",
        "having_single_condition_with_aggregate",
        "having_multiple_conditions_with_aggregate",
        "order_by_multiple_columns",
        "order_by_with_aggregate",
        "join_inner",
        "join_left",
        "join_right",
        "join_full",
        "union",
        "subquery_in_select",
        "subquery_in_where",
        "subquery_in_from",
        "aggregate_count",
        "aggregate_sum",
        "aggregate_avg",
        "aggregate_max",
        "aggregate_min",
        "distinct",
        "case_when",
        "like",
        "in",
        "between",
        "is_null",
        "is_not_null",
    ]
    
    def __init__(self, random_seed: int = 42):
        """初始化生成器"""
        self.random_seed = random_seed
        random.seed(random_seed)
        self.container = DBBenchContainer()
    
    def generate_table_info(self, skill: str) -> TableInfo:
        """根据技能生成表结构"""
        # 根据技能类型生成不同的表结构
        if skill in ["select", "where_single_condition", "where_multiple_conditions"]:
            # 简单的查询表
            columns = [
                ColumnInfo(name="id", type="INT"),
                ColumnInfo(name="name", type="VARCHAR(50)"),
                ColumnInfo(name="age", type="INT"),
                ColumnInfo(name="department", type="VARCHAR(50)"),
            ]
            rows = [
                (1, "Alice", 25, "Engineering"),
                (2, "Bob", 30, "Sales"),
                (3, "Charlie", 28, "Engineering"),
                (4, "Diana", 35, "Marketing"),
                (5, "Eve", 27, "Sales"),
            ]
        elif skill in ["group_by_single_column", "group_by_multiple_columns", "aggregate_count", "aggregate_sum", "aggregate_avg"]:
            # 聚合查询表
            columns = [
                ColumnInfo(name="id", type="INT"),
                ColumnInfo(name="product", type="VARCHAR(50)"),
                ColumnInfo(name="category", type="VARCHAR(50)"),
                ColumnInfo(name="price", type="DECIMAL(10,2)"),
                ColumnInfo(name="quantity", type="INT"),
            ]
            rows = [
                (1, "Laptop", "Electronics", 999.99, 10),
                (2, "Mouse", "Electronics", 29.99, 50),
                (3, "Keyboard", "Electronics", 79.99, 30),
                (4, "Desk", "Furniture", 299.99, 5),
                (5, "Chair", "Furniture", 199.99, 15),
            ]
        elif skill in ["join_inner", "join_left", "join_right", "join_full"]:
            # JOIN查询需要多个表，这里生成主表
            columns = [
                ColumnInfo(name="id", type="INT"),
                ColumnInfo(name="name", type="VARCHAR(50)"),
                ColumnInfo(name="dept_id", type="INT"),
            ]
            rows = [
                (1, "Alice", 1),
                (2, "Bob", 2),
                (3, "Charlie", 1),
                (4, "Diana", 3),
            ]
        else:
            # 默认表结构
            columns = [
                ColumnInfo(name="id", type="INT"),
                ColumnInfo(name="name", type="VARCHAR(50)"),
                ColumnInfo(name="value", type="INT"),
            ]
            rows = [
                (1, "Item1", 100),
                (2, "Item2", 200),
                (3, "Item3", 150),
            ]
        
        table_name = f"table_{random.randint(1000, 9999)}"
        return TableInfo(
            name=table_name,
            column_info_list=columns,
            row_list=rows
        )
    
    def generate_sql(self, skill: str, table_info: TableInfo) -> str:
        """根据技能生成SQL查询"""
        table_name = table_info.name
        columns = table_info.column_info_list
        
        if skill == "select":
            return f"SELECT * FROM `{table_name}`;"
        
        elif skill == "where_single_condition":
            col = columns[1].name  # name
            return f"SELECT * FROM `{table_name}` WHERE `{col}` = 'Alice';"
        
        elif skill == "where_multiple_conditions":
            col1 = columns[1].name  # name
            col2 = columns[2].name  # age
            return f"SELECT * FROM `{table_name}` WHERE `{col1}` = 'Alice' AND `{col2}` > 20;"
        
        elif skill == "order_by_single_column":
            col = columns[1].name
            return f"SELECT * FROM `{table_name}` ORDER BY `{col}` ASC;"
        
        elif skill == "limit_only":
            return f"SELECT * FROM `{table_name}` LIMIT 3;"
        
        elif skill == "group_by_single_column":
            col = columns[2].name  # category
            return f"SELECT `{col}`, COUNT(*) FROM `{table_name}` GROUP BY `{col}`;"
        
        elif skill == "aggregate_count":
            return f"SELECT COUNT(*) FROM `{table_name}`;"
        
        elif skill == "aggregate_sum":
            col = columns[3].name  # price
            return f"SELECT SUM(`{col}`) FROM `{table_name}`;"
        
        elif skill == "aggregate_avg":
            col = columns[3].name  # price
            return f"SELECT AVG(`{col}`) FROM `{table_name}`;"
        
        elif skill == "distinct":
            col = columns[1].name
            return f"SELECT DISTINCT `{col}` FROM `{table_name}`;"
        
        elif skill == "like":
            col = columns[1].name
            return f"SELECT * FROM `{table_name}` WHERE `{col}` LIKE 'A%';"
        
        elif skill == "in":
            col = columns[1].name
            return f"SELECT * FROM `{table_name}` WHERE `{col}` IN ('Alice', 'Bob');"
        
        elif skill == "between":
            col = columns[2].name  # age
            return f"SELECT * FROM `{table_name}` WHERE `{col}` BETWEEN 25 AND 30;"
        
        elif skill == "is_null":
            col = columns[1].name
            return f"SELECT * FROM `{table_name}` WHERE `{col}` IS NULL;"
        
        elif skill == "is_not_null":
            col = columns[1].name
            return f"SELECT * FROM `{table_name}` WHERE `{col}` IS NOT NULL;"
        
        elif skill == "insert":
            col_names = ", ".join([f"`{col.name}`" for col in columns])
            values = ", ".join([f"'{val}'" if isinstance(val, str) else str(val) for val in table_info.row_list[0]])
            return f"INSERT INTO `{table_name}` ({col_names}) VALUES ({values});"
        
        elif skill == "update":
            col1 = columns[1].name
            col2 = columns[2].name
            return f"UPDATE `{table_name}` SET `{col1}` = 'Updated' WHERE `{col2}` > 25;"
        
        elif skill == "delete":
            col = columns[2].name
            return f"DELETE FROM `{table_name}` WHERE `{col}` < 30;"
        
        else:
            # 默认SQL
            return f"SELECT * FROM `{table_name}`;"
    
    def generate_instruction(self, skill: str, sql: str, table_info: TableInfo) -> str:
        """生成自然语言指令"""
        table_name = table_info.name
        columns = [col.name for col in table_info.column_info_list]
        
        if skill == "select":
            return f"Show me all records from the {table_name} table."
        
        elif skill == "where_single_condition":
            return f"Find all records in {table_name} where {columns[1]} equals 'Alice'."
        
        elif skill == "where_multiple_conditions":
            return f"Find all records in {table_name} where {columns[1]} is 'Alice' and {columns[2]} is greater than 20."
        
        elif skill == "order_by_single_column":
            return f"Show all records from {table_name} sorted by {columns[1]} in ascending order."
        
        elif skill == "limit_only":
            return f"Show the first 3 records from {table_name}."
        
        elif skill == "group_by_single_column":
            return f"Count the number of records in {table_name} grouped by {columns[2]}."
        
        elif skill == "aggregate_count":
            return f"How many records are in the {table_name} table?"
        
        elif skill == "aggregate_sum":
            return f"What is the total sum of {columns[3]} in {table_name}?"
        
        elif skill == "aggregate_avg":
            return f"What is the average value of {columns[3]} in {table_name}?"
        
        elif skill == "distinct":
            return f"Show all unique values of {columns[1]} from {table_name}."
        
        elif skill == "like":
            return f"Find all records in {table_name} where {columns[1]} starts with 'A'."
        
        elif skill == "in":
            return f"Find all records in {table_name} where {columns[1]} is either 'Alice' or 'Bob'."
        
        elif skill == "between":
            return f"Find all records in {table_name} where {columns[2]} is between 25 and 30."
        
        elif skill == "insert":
            return f"Add a new record to the {table_name} table."
        
        elif skill == "update":
            return f"Update records in {table_name} where {columns[2]} is greater than 25."
        
        elif skill == "delete":
            return f"Delete records from {table_name} where {columns[2]} is less than 30."
        
        else:
            return f"Query the {table_name} table."
    
    def execute_sql_and_get_answer(self, sql: str, table_info: TableInfo, database_name: str, skill: str) -> tuple[Optional[List], Optional[str]]:
        """执行SQL并获取答案"""
        try:
            # 确定答案类型
            sql_upper = sql.strip().upper()
            if sql_upper.startswith("SELECT"):
                answer_type = AnswerType.DIRECT
            else:
                answer_type = AnswerType.MD5
            
            # 创建数据库和表
            dataset_item = DBBenchDatasetItem(
                instruction="",
                answer_info=AnswerInfo(
                    answer_type=answer_type,
                    answer_direct=None,
                    answer_md5=None,
                    ground_truth_sql=sql
                ),
                database_name=database_name,
                table_info=table_info,
                skill_list=[skill]
            )
            init_sql = DBBench._build_init_sql(dataset_item)
            self.container.execute(init_sql)
            
            # 执行查询SQL
            if sql_upper.startswith("SELECT"):
                result = self.container.execute(sql, database=database_name)
                # 解析结果 - result是字符串，需要转换为列表
                try:
                    import ast
                    # 尝试解析为Python列表
                    answer_direct = ast.literal_eval(result)
                    if isinstance(answer_direct, list):
                        return answer_direct, None
                    else:
                        return None, None
                except:
                    # 如果解析失败，返回空列表
                    return [], None
            else:
                # INSERT/UPDATE/DELETE 需要计算MD5
                # 先获取原始表的MD5
                check_sql = f"SELECT * FROM `{table_info.name}` ORDER BY `{table_info.column_info_list[0].name}`;"
                original_result = self.container.execute(check_sql, database=database_name)
                original_md5 = hashlib.md5(str(original_result).encode()).hexdigest()
                
                # 执行修改操作
                self.container.execute(sql, database=database_name)
                
                # 获取执行后的表MD5
                executed_result = self.container.execute(check_sql, database=database_name)
                executed_md5 = hashlib.md5(str(executed_result).encode()).hexdigest()
                
                return (original_md5, executed_md5), None
            
        except Exception as e:
            return None, str(e)
        finally:
            # 清理数据库
            try:
                self.container.execute(f"DROP DATABASE IF EXISTS `{database_name}`;")
            except:
                pass
    
    def generate_single_entry(self, skill: str, entry_index: int) -> Dict[str, Any]:
        """生成单个数据条目"""
        # 生成表结构
        table_info = self.generate_table_info(skill)
        database_name = table_info.name
        
        # 生成SQL
        sql = self.generate_sql(skill, table_info)
        
        # 执行SQL获取答案
        result, error = self.execute_sql_and_get_answer(sql, table_info, database_name, skill)
        
        if error:
            print(f"Warning: SQL execution failed for entry {entry_index}: {error}")
            result = None
        
        # 生成指令
        instruction = self.generate_instruction(skill, sql, table_info)
        
        # 确定答案类型和值
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            answer_type = AnswerType.DIRECT
            answer_direct = result if result is not None else []
            answer_md5 = None
        else:
            answer_type = AnswerType.MD5
            answer_direct = None
            if result is not None and isinstance(result, tuple):
                # result是(original_md5, executed_md5)
                answer_md5 = result[1]  # 使用执行后的MD5
            else:
                # 如果获取失败，使用SQL的MD5作为fallback
                answer_md5 = hashlib.md5(sql.encode()).hexdigest()
        
        # 构建entry
        entry = {
            "answer_info": {
                "direct": answer_direct,
                "md5": answer_md5,
                "sql": sql,
            },
            "table_info": {
                "name": table_info.name,
                "column_info_list": [
                    {"name": col.name, "type": col.type}
                    for col in table_info.column_info_list
                ],
                "row_list": [list(row) for row in table_info.row_list],
            },
            "instruction": instruction,
            "skill_list": [skill],  # 只包含一个skill
        }
        
        return entry
    
    def generate_dataset(
        self,
        num_samples: int,
        skills: Optional[List[str]] = None,
        balance_skills: bool = True
    ) -> Dict[str, Any]:
        """生成数据集"""
        if skills is None:
            skills = self.ALL_SKILLS
        
        # 验证技能
        valid_skills = [s for s in skills if DBBenchSkillUtility.is_valid_skill(s)]
        if not valid_skills:
            raise ValueError("No valid skills provided")
        
        print(f"Generating {num_samples} samples...")
        print(f"Using {len(valid_skills)} skills: {valid_skills[:5]}...")
        
        entry_dict = {}
        
        if balance_skills:
            # 平衡分配技能
            samples_per_skill = num_samples // len(valid_skills)
            remainder = num_samples % len(valid_skills)
            
            skill_counts = {}
            for i, skill in enumerate(valid_skills):
                count = samples_per_skill + (1 if i < remainder else 0)
                skill_counts[skill] = count
            
            entry_index = 0
            for skill, count in skill_counts.items():
                print(f"  Generating {count} samples for skill '{skill}'...")
                for _ in range(count):
                    entry = self.generate_single_entry(skill, entry_index)
                    entry_dict[str(entry_index)] = entry
                    entry_index += 1
                    if entry_index % 10 == 0:
                        print(f"    Generated {entry_index}/{num_samples} samples...")
        else:
            # 随机分配技能
            for entry_index in range(num_samples):
                skill = random.choice(valid_skills)
                entry = self.generate_single_entry(skill, entry_index)
                entry_dict[str(entry_index)] = entry
                if (entry_index + 1) % 10 == 0:
                    print(f"  Generated {entry_index + 1}/{num_samples} samples...")
        
        return entry_dict


def main():
    parser = argparse.ArgumentParser(
        description="Generate DB bench training data with single skills"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        required=True,
        help="Number of samples to generate"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="./data/v0303/db_bench/processed/generated/entry_dict.json",
        help="Output file path"
    )
    parser.add_argument(
        "--random_seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--skills",
        type=str,
        nargs="+",
        default=None,
        help="Specific skills to generate (default: all skills)"
    )
    parser.add_argument(
        "--no_balance",
        action="store_true",
        help="Don't balance skills (random distribution instead)"
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成数据
    generator = DBBenchDataGenerator(random_seed=args.random_seed)
    
    try:
        entry_dict = generator.generate_dataset(
            num_samples=args.num_samples,
            skills=args.skills,
            balance_skills=not args.no_balance
        )
        
        # 保存数据
        print(f"\nSaving {len(entry_dict)} samples to {output_path}...")
        with open(output_path, "w") as f:
            json.dump(entry_dict, f, indent=2)
        
        # 打印统计信息
        print("\n✓ Generation completed!")
        print(f"  Total samples: {len(entry_dict)}")
        print(f"  Output file: {output_path}")
        
        # 统计技能分布
        skill_distribution = {}
        for entry in entry_dict.values():
            skill = entry["skill_list"][0]
            skill_distribution[skill] = skill_distribution.get(skill, 0) + 1
        
        print("\nSkill distribution:")
        for skill, count in sorted(skill_distribution.items()):
            print(f"  {skill}: {count}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理容器
        try:
            generator.container.delete()
        except:
            pass


if __name__ == "__main__":
    main()

