# Agent-PEFT: LoRA + RL Training for DB Bench

基于 LifelongAgentBench 框架，使用 LoRA (Low-Rank Adaptation) 和强化学习 (RL) 实现 Agent 在 DB bench 环境中的持续学习。

## 已完成功能

- ✅ LoRA 语言模型集成 (`HuggingfaceLoRALanguageModel`)
- ✅ RL 训练回调 (`RLTrainingCallback`) - 基于 REINFORCE 算法
- ✅ LoRA + RL Agent (`LoRARLAgent`)
- ✅ Single-skill 任务生成器 (`DBBenchSingleSkill`)
- ✅ 完整的数据生成脚本
- ✅ 实验配置和运行脚本

## 快速开始

### 1. 环境配置

#### 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `peft>=0.10.0` - LoRA 支持
- `torch` - PyTorch
- `transformers` - HuggingFace Transformers
- `datasets` - HuggingFace Datasets (可选，用于下载数据)
- `docker` - MySQL 容器支持
- `mysql-connector-python` - MySQL 连接

#### Docker 配置

确保 Docker 和 MySQL 镜像已准备：

```bash
# 检查 Docker
docker ps

# 拉取 MySQL 镜像（如果未拉取）
docker pull mysql:latest
```

### 2. 生成 Single-Skill DB 数据

#### 方法1: 使用数据生成脚本（推荐）

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

### 3. 配置实验

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

### 4. 开始训练

#### 使用一键脚本（推荐）

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

## 项目结构

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

## 核心组件说明

### LoRA + RL 训练流程

1. **初始化**: 加载基础模型，添加零初始化的 LoRA 适配器
2. **推理**: Agent 使用 LoRA 模型进行推理，记录 log probabilities
3. **评估**: 任务完成后评估结果（CORRECT/INCORRECT）
4. **奖励计算**: 根据结果计算奖励（成功 +1.0，失败 -0.1）
5. **参数更新**: 使用 REINFORCE 算法更新 LoRA 参数
6. **保存**: 定期保存 LoRA 权重和优化器状态

### 关键配置参数

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

## 故障排除

### 常见问题

1. **Docker 错误**: 确保 Docker daemon 运行，MySQL 镜像已拉取
2. **数据未找到**: 运行数据生成脚本或检查数据路径配置
3. **模块导入错误**: 确保设置了 `PYTHONPATH` 或从项目根目录运行
4. **模型路径错误**: 检查配置文件中的模型路径是否正确

### 详细文档

- 数据生成: `docs/GENERATE_DATA_GUIDE.md`
- 数据准备: `docs/DATA_PREPARATION_GUIDE.md`
- Docker 配置: `docs/DOCKER_FIX.md`

## 引用

基于 [LifelongAgentBench](https://github.com/caixd-220529/continual_agent_bench) 框架。

## License

遵循原项目许可证。
