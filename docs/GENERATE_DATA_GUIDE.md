# DB Bench 数据生成脚本使用指南

## 概述

`scripts/generate_db_bench_data.py` 是一个完整的数据生成脚本，用于生成符合要求的 DB bench 训练数据。

## 功能特点

- ✅ 可指定生成数量
- ✅ 每个样本包含且仅包含一个 skill
- ✅ 包含 instruction（自然语言指令）
- ✅ 包含 ground truth SQL（正确的SQL查询）
- ✅ 包含 skill list（技能列表）
- ✅ 自动执行SQL验证答案
- ✅ 支持技能平衡分配或随机分配
- ✅ 保存到标准位置

## 使用方法

### 基本用法

```bash
cd /root/Agent-PEFT

# 生成100个样本
python3 scripts/generate_db_bench_data.py --num_samples 100

# 指定输出路径
python3 scripts/generate_db_bench_data.py \
    --num_samples 100 \
    --output_path ./data/v0303/db_bench/processed/generated/entry_dict.json

# 指定随机种子（确保可复现）
python3 scripts/generate_db_bench_data.py \
    --num_samples 100 \
    --random_seed 42
```

### 高级用法

```bash
# 只生成特定技能的数据
python3 scripts/generate_db_bench_data.py \
    --num_samples 50 \
    --skills select where_single_condition group_by_single_column

# 随机分配技能（不平衡）
python3 scripts/generate_db_bench_data.py \
    --num_samples 100 \
    --no_balance
```

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--num_samples` | int | ✅ | - | 要生成的样本数量 |
| `--output_path` | str | ❌ | `./data/v0303/db_bench/processed/generated/entry_dict.json` | 输出文件路径 |
| `--random_seed` | int | ❌ | 42 | 随机种子 |
| `--skills` | list[str] | ❌ | 所有技能 | 指定要生成的技能列表 |
| `--no_balance` | flag | ❌ | False | 不平衡分配技能（随机分配） |

## 支持的技能列表

脚本支持以下所有技能：

- **基础操作**: `select`, `insert`, `delete`, `update`
- **WHERE条件**: `where_single_condition`, `where_multiple_conditions`, `where_nested_conditions`
- **排序和限制**: `order_by_single_column`, `limit_only`, `limit_and_offset`
- **分组**: `group_by_single_column`, `group_by_multiple_columns`
- **聚合函数**: `aggregate_count`, `aggregate_sum`, `aggregate_avg`, `aggregate_max`, `aggregate_min`
- **HAVING**: `having_single_condition_with_aggregate`, `having_multiple_conditions_with_aggregate`
- **JOIN**: `join_inner`, `join_left`, `join_right`, `join_full`
- **子查询**: `subquery_in_select`, `subquery_in_where`, `subquery_in_from`
- **其他**: `distinct`, `case_when`, `like`, `in`, `between`, `is_null`, `is_not_null`, `column_alias`, `table_alias`, `union`

## 输出格式

生成的 `entry_dict.json` 文件格式如下：

```json
{
  "0": {
    "answer_info": {
      "direct": [[1, "Alice", 25, "Engineering"]],
      "md5": null,
      "sql": "SELECT * FROM `table_1234`;"
    },
    "table_info": {
      "name": "table_1234",
      "column_info_list": [
        {"name": "id", "type": "INT"},
        {"name": "name", "type": "VARCHAR(50)"},
        {"name": "age", "type": "INT"},
        {"name": "department", "type": "VARCHAR(50)"}
      ],
      "row_list": [
        [1, "Alice", 25, "Engineering"],
        [2, "Bob", 30, "Sales"]
      ]
    },
    "instruction": "Show me all records from the table_1234 table.",
    "skill_list": ["select"]
  },
  "1": { ... }
}
```

## 数据验证

脚本会自动：
1. 创建数据库和表
2. 执行生成的SQL查询
3. 验证结果并提取答案
4. 对于SELECT查询，返回直接答案（direct）
5. 对于INSERT/UPDATE/DELETE，计算MD5值

## 技能分配策略

### 平衡分配（默认）

默认情况下，脚本会平衡分配技能，确保每个技能都有大致相同数量的样本：

```bash
# 生成100个样本，使用10个技能
# 每个技能分配10个样本
python3 scripts/generate_db_bench_data.py --num_samples 100
```

### 随机分配

使用 `--no_balance` 标志可以随机分配技能：

```bash
# 随机分配技能
python3 scripts/generate_db_bench_data.py --num_samples 100 --no_balance
```

## 示例

### 示例1: 生成小规模测试数据

```bash
python3 scripts/generate_db_bench_data.py \
    --num_samples 20 \
    --output_path ./data/v0303/db_bench/processed/test/entry_dict.json \
    --random_seed 123
```

### 示例2: 生成特定技能的训练数据

```bash
python3 scripts/generate_db_bench_data.py \
    --num_samples 50 \
    --skills select where_single_condition group_by_single_column aggregate_count \
    --output_path ./data/v0303/db_bench/processed/specific_skills/entry_dict.json
```

### 示例3: 生成大规模数据集

```bash
python3 scripts/generate_db_bench_data.py \
    --num_samples 1000 \
    --output_path ./data/v0303/db_bench/processed/large/entry_dict.json \
    --random_seed 42
```

## 注意事项

1. **Docker要求**: 脚本需要Docker和MySQL容器运行，确保Docker daemon正在运行
2. **执行时间**: 生成大量数据可能需要较长时间，因为每个样本都需要执行SQL验证
3. **数据库清理**: 脚本会自动清理临时数据库，但如果中途中断，可能需要手动清理
4. **错误处理**: 如果SQL执行失败，脚本会记录警告但继续生成其他样本

## 故障排除

### Docker未运行

```bash
# 检查Docker状态
docker ps

# 如果未运行，启动Docker
sudo systemctl start docker
```

### MySQL镜像未拉取

```bash
# 拉取MySQL镜像
docker pull mysql:latest
```

### 权限问题

```bash
# 确保有Docker权限
sudo usermod -aG docker $USER
# 重新登录或运行
newgrp docker
```

## 后续步骤

生成数据后，可以：

1. **准备single-skill数据**（如果需要）:
   ```bash
   python3 scripts/prepare_single_skill_data.py \
       --input_data_path ./data/v0303/db_bench/processed/generated/entry_dict.json \
       --output_path ./data/v0303/db_bench/processed/generated/single_skill_tasks.json
   ```

2. **更新配置文件**使用生成的数据:
   ```yaml
   # configs/components/tasks/db_bench_single_skill.yaml
   parameters:
     single_skill_task_generator:
       parameters:
         skill_to_tasks_path: "./data/v0303/db_bench/processed/generated/single_skill_tasks.json"
   ```

3. **运行实验**:
   ```bash
   bash scripts/run_rl_training_qwen25_7b.sh
   ```

## 相关文件

- `scripts/generate_db_bench_data.py` - 数据生成脚本
- `scripts/prepare_single_skill_data.py` - Single-skill数据准备脚本
- `src/tasks/instance/db_bench/task.py` - DB bench任务定义
- `src/tasks/instance/db_bench/container.py` - Docker容器管理

