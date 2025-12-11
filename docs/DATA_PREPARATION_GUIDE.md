# 数据准备完整指南

本指南介绍如何准备 DB bench 实验所需的数据。

## 方法1: 从 HuggingFace 数据集下载（推荐）

### 步骤1: 安装依赖

```bash
pip install datasets
```

### 步骤2: 下载并转换数据

使用提供的脚本自动下载和转换：

```bash
cd /root/Agent-PEFT
python3 scripts/download_huggingface_data.py \
    --output_dir ./data/v0303/db_bench/processed/huggingface \
    --split train
```

或者手动指定参数：

```bash
python3 scripts/download_huggingface_data.py \
    --output_dir ./data/v0303/db_bench/processed/huggingface \
    --split train \
    --dataset_name csyq/LifelongAgentBench
```

### 步骤3: 验证数据

下载完成后，检查生成的文件：

```bash
ls -lh ./data/v0303/db_bench/processed/huggingface/entry_dict.json
```

### 步骤4: 准备 single-skill 数据

如果需要进行 single-skill 实验，运行：

```bash
python3 scripts/prepare_single_skill_data.py \
    --input_data_path ./data/v0303/db_bench/processed/huggingface/entry_dict.json \
    --output_path ./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json \
    --min_tasks_per_skill 1
```

### 步骤5: 更新配置文件

如果使用不同的数据路径，需要更新配置文件中的 `data_file_path`：

```yaml
# configs/components/tasks/db_bench_single_skill.yaml
parameters:
  single_skill_task_generator:
    parameters:
      skill_to_tasks_path: "./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json"
```

---

## 方法2: 使用数据工厂生成（完整流程）

数据工厂可以生成完整的数据集，但需要更多步骤和依赖。

### 前置条件

1. **Docker**: MySQL 容器需要运行
2. **OpenAI API**: 某些步骤可能需要 OpenAI API（用于生成指令）
3. **时间**: 完整生成过程可能需要较长时间

### 数据工厂流程

数据工厂包含多个步骤，按顺序执行：

#### 步骤1: SQL Factory
生成 SQL 查询和表结构

```bash
python3 -m src.factories.data.standard_v0303.instance.db_bench.sql_factory
```

#### 步骤2: Instruction Factory
为 SQL 生成自然语言指令

```bash
python3 -m src.factories.data.standard_v0303.instance.db_bench.instruction_factory
```

#### 步骤3: Row List Factory
生成行数据并验证

```bash
python3 -m src.factories.data.standard_v0303.instance.db_bench.row_list_factory
```

#### 步骤4: Entry Factory
整合所有数据并生成最终的 entry_dict.json

```bash
python3 -m src.factories.data.standard_v0303.instance.db_bench.entry_factory
```

### Entry Factory 配置

查看 `entry_factory.py` 的 `main()` 函数，可以看到默认配置：

```python
entry_factory = EntryFactory(
    row_list_factory_output_dir="data/v0303/db_bench/raw/row_list_factory/v0316",
    output_dir="data/v0303/db_bench/processed/v0317_first500",
    log_file_path="./outputs/data/v0303/db_bench/entry_factory.log",
    random_seed=0,
)
entry_factory.random_order_construct(sample_count=500)
```

### 自定义数据生成

如果需要自定义，可以修改 `entry_factory.py` 的 `main()` 函数：

```python
def main() -> None:
    entry_factory = EntryFactory(
        row_list_factory_output_dir="your/row_list/path",
        output_dir="your/output/path",
        log_file_path="./outputs/data/v0303/db_bench/entry_factory.log",
        random_seed=42,  # 自定义随机种子
    )
    entry_factory.random_order_construct(sample_count=1000)  # 自定义样本数量
    # entry_factory.validate()  # 取消注释以验证数据
```

---

## 方法3: 使用最小测试数据（快速测试）

如果只是想快速测试，可以使用最小测试数据：

```bash
python3 scripts/create_minimal_test_data.py \
    --output_path ./data/v0303/db_bench/processed/test/entry_dict.json \
    --num_samples 10
```

---

## 数据格式说明

### entry_dict.json 格式

```json
{
  "0": {
    "answer_info": {
      "direct": "答案内容（如果是直接答案类型）",
      "md5": "答案的MD5哈希（如果是MD5类型）",
      "sql": "正确的SQL查询"
    },
    "table_info": {
      "name": "表名",
      "column_info_list": [
        {
          "name": "列名",
          "type": "数据类型"
        }
      ],
      "row_list": [
        ["值1", "值2", ...]
      ]
    },
    "instruction": "自然语言问题/指令",
    "skill_list": ["技能1", "技能2"]
  },
  "1": { ... }
}
```

### single_skill_tasks.json 格式

```json
{
  "技能名称1": {
    "任务ID1": { ... },
    "任务ID2": { ... }
  },
  "技能名称2": {
    ...
  }
}
```

---

## 常见问题

### Q: HuggingFace 下载失败
**A**: 
1. 检查网络连接
2. 如果在中国，可能需要配置代理或使用镜像
3. 尝试手动下载：访问 https://huggingface.co/datasets/csyq/LifelongAgentBench

### Q: 数据工厂生成失败
**A**:
1. 确保 Docker 和 MySQL 容器正常运行
2. 检查 OpenAI API 配置（如果使用）
3. 查看日志文件：`./outputs/data/v0303/db_bench/entry_factory.log`

### Q: 数据路径不匹配
**A**: 
1. 检查配置文件中的路径是否正确
2. 使用绝对路径或确保相对路径正确
3. 运行脚本时确保在项目根目录

### Q: 如何验证数据是否正确
**A**: 
在 `entry_factory.py` 中取消注释验证代码：
```python
entry_factory.validate()
```

---

## 推荐工作流

1. **快速开始**: 使用方法1（HuggingFace下载）
2. **完整实验**: 使用方法1下载完整数据集
3. **自定义数据**: 使用方法2（数据工厂）
4. **快速测试**: 使用方法3（最小测试数据）

---

## 相关文件

- `scripts/download_huggingface_data.py` - HuggingFace 数据下载脚本
- `scripts/prepare_single_skill_data.py` - Single-skill 数据准备脚本
- `scripts/create_minimal_test_data.py` - 最小测试数据生成脚本
- `src/factories/data/standard_v0303/instance/db_bench/entry_factory.py` - 数据工厂入口

