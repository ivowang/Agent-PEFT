# Agent-PEFT

## Quick Start

### 1. Set up

```bash
pip install -r requirements.txt

docker pull mysql:latest
```

### 2. Single-Skill DB Generation

#### 方法1: 使用数据生成脚本

```bash
# 生成指定数量的 single-skill 数据
python3 scripts/generate_db_bench_data.py \
    --num_samples 100 \
    --output_path ./data/v0303/db_bench/processed/generated/entry_dict.json

# 准备 single-skill 任务文件
python3 scripts/prepare_single_skill_data.py \
    --input_data_path ./data/v0303/db_bench/processed/generated/entry_dict.json \
    --output_path ./data/v0303/db_bench/processed/generated/single_skill_tasks.json \
    --min_tasks_per_skill 1
```

#### 方法2: 从 HuggingFace 下载

```bash
# 下载并转换数据
python3 scripts/download_huggingface_data.py \
    --output_dir ./data/v0303/db_bench/processed/huggingface

# 准备 single-skill 任务
python3 scripts/prepare_single_skill_data.py \
    --input_data_path ./data/v0303/db_bench/processed/huggingface/entry_dict.json \
    --output_path ./data/v0303/db_bench/processed/huggingface/single_skill_tasks.json
```

### 3. Configuration

#### 更新配置文件

编辑 `configs/components/tasks/db_bench_single_skill.yaml`，确保数据路径正确：

```yaml
parameters:
  single_skill_task_generator:
    parameters:
      skill_to_tasks_path: "./data/v0303/db_bench/processed/generated/single_skill_tasks.json"
```

或直接编辑实验配置文件 `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml`。

#### 检查模型路径

确保 `configs/components/language_models/huggingface_lora_language_model.yaml` 中的模型路径正确：

```yaml
Qwen2.5-7B-Instruct-LoRA:
  parameters:
    model_name_or_path: "/path/to/Qwen2.5-7B-Instruct"
```

### 4. Start Training

```bash
bash scripts/run_rl_training_qwen25_7b.sh
```

脚本会自动：
1. 检查数据文件
2. 准备 single-skill 数据（如果不存在）
3. 检查 Docker 和 MySQL 镜像
4. 检查 Python 依赖
5. 运行实验

#### 手动运行

```bash
# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 运行实验
python3 src/run_experiment.py \
    --config_path configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml
```

## 关键参数

- **LoRA 配置** (`huggingface_lora_language_model.yaml`):
  - `r`: LoRA 秩（默认 16）
  - `lora_alpha`: LoRA alpha（默认 32）
  - `target_modules`: 目标模块（默认 ["q_proj", "v_proj", "k_proj", "o_proj"]）

- **RL 配置** (`rl_training_callback.yaml`):
  - `reward_correct`: 成功奖励（默认 1.0）
  - `reward_incorrect`: 失败惩罚（默认 -0.1）
  - `learning_rate`: 学习率（默认 0.00001）

## 输出结果

实验输出保存在：
```
outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/
├── sessions/              # 会话记录
├── checkpoints/           # LoRA 权重检查点
└── logs/                  # 训练日志
```

## 相对于LifelongBench的新增代码

```
Agent-PEFT/
├── src/
│   ├── language_models/instance/
│   │   └── huggingface_lora_language_model.py  # LoRA 语言模型
│   ├── agents/instance/
│   │   └── lora_rl_agent.py                     # LoRA + RL Agent
│   ├── callbacks/instance/
│   │   └── rl_training_callback.py              # RL 训练回调
│   └── tasks/instance/db_bench/
│       ├── task_single_skill.py                 # Single-skill 任务
│       └── single_skill_task_generator.py       # 任务生成器
├── scripts/
│   ├── generate_db_bench_data.py                # 数据生成脚本
│   ├── prepare_single_skill_data.py             # Single-skill 数据准备
│   ├── download_huggingface_data.py             # HuggingFace 数据下载
│   └── run_rl_training_qwen25_7b.sh             # 一键运行脚本
├── configs/
│   ├── components/
│   │   ├── language_models/
│   │   │   └── huggingface_lora_language_model.yaml
│   │   ├── agents/
│   │   │   └── lora_rl_agent.yaml
│   │   ├── callbacks/
│   │   │   └── rl_training_callback.yaml
│   │   └── tasks/
│   │       └── db_bench_single_skill.yaml
│   └── assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/
│       └── rl_training.yaml                      # 主实验配置
└── data/
    └── v0303/db_bench/processed/                 # 数据目录
```
