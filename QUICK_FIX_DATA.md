# 数据问题快速解决方案

## 问题
数据文件不存在：`./data/v0303/db_bench/processed/v0317_first500/entry_dict.json`

## 解决方案

### 方案1: 自动创建测试数据（推荐，快速测试）

运行脚本会自动创建最小测试数据：

```bash
cd /root/Agent-PEFT
bash scripts/run_rl_training_qwen25_7b.sh
```

脚本会自动：
1. 检测数据文件不存在
2. 创建包含10个样本的最小测试数据集
3. 继续运行实验

### 方案2: 手动创建测试数据

```bash
cd /root/Agent-PEFT

# 创建最小测试数据
python scripts/create_minimal_test_data.py \
    --output_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --num_samples 10

# 然后运行实验
bash scripts/run_rl_training_qwen25_7b.sh
```

### 方案3: 使用完整数据生成流程（如果有原始数据）

如果你有原始数据（`row_list_factory`的输出），可以运行完整的数据生成：

```bash
cd /root/Agent-PEFT

# 运行EntryFactory生成数据
python -m src.factories.data.standard_v0303.instance.db_bench.entry_factory
```

### 方案4: 使用其他位置的数据

如果你在其他位置有数据，可以修改配置文件：

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

## 数据说明

### 测试数据 vs 完整数据

- **测试数据** (`create_minimal_test_data.py`): 
  - 包含5-10个简单的single-skill tasks
  - 用于快速测试RL训练功能
  - 不适合完整实验评估

- **完整数据** (通过数据工厂生成):
  - 包含大量多样化的tasks
  - 覆盖所有技能类型
  - 适合完整实验和评估

### 数据来源

根据README，数据可以通过以下方式获得：
1. **HuggingFace数据集**: https://huggingface.co/datasets/csyq/LifelongAgentBench
2. **数据工厂生成**: 使用项目中的数据生成流程

## 下一步

1. **快速测试**: 使用方案1或2创建测试数据
2. **完整实验**: 
   - 从HuggingFace下载数据，或
   - 运行完整的数据生成流程

## 验证数据

创建数据后，可以验证：

```bash
# 检查文件是否存在
ls -lh data/v0303/db_bench/processed/v0317_first500/entry_dict.json

# 检查数据格式
python -c "
import json
with open('data/v0303/db_bench/processed/v0317_first500/entry_dict.json') as f:
    data = json.load(f)
    print(f'Found {len(data)} samples')
    if len(data) > 0:
        sample = list(data.values())[0]
        print(f'Sample keys: {list(sample.keys())}')
        print(f'Skills: {sample.get(\"skill_list\", [])}')
"
```

