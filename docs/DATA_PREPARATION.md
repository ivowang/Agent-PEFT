# DB Benchmark数据准备指南

## 数据来源说明

DB benchmark的数据**不是下载的**，而是通过数据工厂（Data Factory）**生成**的。

数据生成流程：
1. **SQLFactory** → 生成SQL语句和表结构
2. **InstructionFactory** → 基于SQL生成自然语言指令
3. **RowListFactory** → 生成数据行
4. **EntryFactory** → 整合所有数据，生成最终的 `entry_dict.json`

## 数据生成方法

### 方法1: 使用完整数据生成流程（推荐，如果原始数据存在）

如果你有原始数据（`row_list_factory`的输出），可以运行：

```bash
cd /root/Agent-PEFT

# 运行EntryFactory生成数据
python -m src.factories.data.standard_v0303.instance.db_bench.entry_factory
```

这会生成：
- `data/v0303/db_bench/processed/v0317_first500/entry_dict.json`

### 方法2: 使用已有数据（如果有）

如果你在其他地方有已生成的数据，可以：
1. 创建数据目录结构
2. 复制数据文件到对应位置

```bash
mkdir -p data/v0303/db_bench/processed/v0317_first500
cp /path/to/your/entry_dict.json data/v0303/db_bench/processed/v0317_first500/
```

### 方法3: 使用简化数据生成脚本（快速测试）

如果只是想快速测试RL训练功能，可以使用简化版本：

```bash
# 创建最小测试数据集
python scripts/create_minimal_test_data.py
```

## 数据目录结构

```
data/
└── v0303/
    └── db_bench/
        └── processed/
            └── v0317_first500/
                └── entry_dict.json  # 这是我们需要的数据文件
```

## 快速解决方案

### 选项A: 创建最小测试数据

创建一个包含少量single-skill tasks的测试数据集：

```bash
python scripts/create_minimal_test_data.py \
    --output_path data/v0303/db_bench/processed/v0317_first500/entry_dict.json \
    --num_samples 10
```

### 选项B: 修改配置使用其他数据路径

如果你有其他位置的数据，可以修改配置文件：

1. 修改 `configs/components/tasks/db_bench.yaml`:
```yaml
data_file_path: "/your/path/to/entry_dict.json"
```

2. 修改 `configs/components/tasks/db_bench_single_skill.yaml`:
```yaml
single_skill_task_generator:
  parameters:
    skill_to_tasks_path: "/your/path/to/single_skill_tasks.json"
```

## 数据格式说明

`entry_dict.json` 的格式示例：

```json
{
  "0": {
    "answer_info": {
      "direct": [["Alice", 25]],
      "md5": null,
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
        ["Bob", 30]
      ]
    },
    "instruction": "Find all users older than 20 years old.",
    "skill_list": ["select", "where_single_condition"]
  }
}
```

## 检查数据是否存在

```bash
# 检查数据文件
ls -lh data/v0303/db_bench/processed/v0317_first500/entry_dict.json

# 检查数据格式
python -c "
import json
with open('data/v0303/db_bench/processed/v0317_first500/entry_dict.json') as f:
    data = json.load(f)
    print(f'Found {len(data)} samples')
    print(f'Sample keys: {list(data.keys())[:5]}')
"
```

## 下一步

1. **如果有原始数据**: 运行完整的数据生成流程
2. **如果没有数据**: 使用最小测试数据集或联系项目维护者获取数据
3. **如果有其他位置的数据**: 修改配置文件指向你的数据路径

## 注意事项

- 数据生成需要较长时间（特别是大规模数据）
- 确保有足够的磁盘空间
- 如果使用Docker环境，确保数据目录已挂载

