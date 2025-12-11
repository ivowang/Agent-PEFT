# 快速数据设置指南

## 方法1: 从 HuggingFace 下载（最简单，推荐）

### 一键下载

```bash
cd /root/Agent-PEFT

# 1. 安装依赖（如果还没有）
pip install datasets

# 2. 下载并转换数据
python3 scripts/download_huggingface_data.py \
    --output_dir ./data/v0303/db_bench/processed/huggingface

# 3. 准备 single-skill 数据（用于 RL 训练）
python3 scripts/prepare_single_skill_data.py \
    --input_data_path ./data/v0303/db_bench/processed/huggingface/entry_dict.json \
    --output_path ./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json \
    --min_tasks_per_skill 1
```

### 验证数据

```bash
# 检查文件是否存在
ls -lh ./data/v0303/db_bench/processed/huggingface/entry_dict.json
ls -lh ./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json

# 查看数据统计
python3 -c "
import json
with open('./data/v0303/db_bench/processed/huggingface/entry_dict.json') as f:
    data = json.load(f)
    print(f'Total samples: {len(data)}')
    if data:
        first = data['0']
        print(f'Sample skills: {first.get(\"skill_list\", [])}')
"
```

---

## 方法2: 使用数据工厂生成（需要更多步骤）

### 完整流程

数据工厂需要按顺序运行多个步骤：

```bash
cd /root/Agent-PEFT

# 步骤1: SQL Factory（生成 SQL 和表结构）
python3 -m src.factories.data.standard_v0303.instance.db_bench.sql_factory

# 步骤2: Instruction Factory（生成自然语言指令）
python3 -m src.factories.data.standard_v0303.instance.db_bench.instruction_factory

# 步骤3: Row List Factory（生成行数据并验证）
python3 -m src.factories.data.standard_v0303.instance.db_bench.row_list_factory

# 步骤4: Entry Factory（整合数据生成 entry_dict.json）
python3 -m src.factories.data.standard_v0303.instance.db_bench.entry_factory
```

**注意**: 
- 需要 Docker 和 MySQL 容器运行
- 某些步骤可能需要 OpenAI API
- 整个过程可能需要较长时间

### Entry Factory 说明

`entry_factory.py` 的默认配置：

- **输入**: `data/v0303/db_bench/raw/row_list_factory/v0316`
- **输出**: `data/v0303/db_bench/processed/v0317_first500`
- **样本数**: 500
- **随机种子**: 0

如果需要自定义，修改 `entry_factory.py` 的 `main()` 函数。

---

## 方法3: 最小测试数据（快速测试）

```bash
python3 scripts/create_minimal_test_data.py \
    --output_path ./data/v0303/db_bench/processed/test/entry_dict.json \
    --num_samples 10
```

---

## 更新配置文件

如果使用不同的数据路径，需要更新配置文件：

### 对于标准 DB bench 任务

编辑 `configs/components/tasks/db_bench.yaml`:

```yaml
parameters:
  data_file_path: "./data/v0303/db_bench/processed/huggingface/entry_dict.json"
```

### 对于 Single-skill 任务（RL 训练）

编辑 `configs/components/tasks/db_bench_single_skill.yaml`:

```yaml
parameters:
  single_skill_task_generator:
    parameters:
      skill_to_tasks_path: "./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json"
```

或者编辑实验配置文件：

```yaml
# configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml
assignment_config:
  task:
    custom_parameters:
      single_skill_task_generator:
        parameters:
          skill_to_tasks_path: "./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json"
```

---

## 推荐工作流

1. **首次使用**: 使用方法1（HuggingFace下载），最简单快速
2. **完整实验**: 使用方法1下载完整数据集
3. **自定义数据**: 使用方法2（数据工厂），但需要更多配置
4. **快速测试**: 使用方法3（最小测试数据）

---

## 故障排除

### HuggingFace 下载失败

```bash
# 检查网络连接
ping huggingface.co

# 手动安装 datasets
pip install --upgrade datasets

# 如果在中国，可能需要配置代理
export HF_ENDPOINT=https://hf-mirror.com
```

### 数据路径问题

确保：
1. 使用绝对路径或从项目根目录运行
2. 检查配置文件中的路径是否正确
3. 确保数据文件存在：`ls -lh <data_path>`

### 数据格式问题

验证 JSON 格式：
```bash
python3 -c "import json; json.load(open('your_file.json'))"
```

---

## 相关文档

- 完整指南: `docs/DATA_PREPARATION_GUIDE.md`
- 数据工厂代码: `src/factories/data/standard_v0303/instance/db_bench/`

