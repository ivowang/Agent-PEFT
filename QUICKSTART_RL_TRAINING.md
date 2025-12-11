# RL训练快速开始指南

## 一键运行（推荐）

```bash
# 进入项目目录
cd /root/LifelongAgentBench

# 运行自动化脚本
bash scripts/run_rl_training_qwen25_7b.sh
```

脚本会自动完成所有准备工作并运行实验。

## 手动步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 准备数据
```bash
python scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./data/v0303/db_bench/processed/v0317_first500/single_skill_tasks.json"
```

### 3. 检查配置
- 模型路径: `configs/components/language_models/huggingface_lora_language_model.yaml`
- 数据路径: `configs/components/tasks/db_bench_single_skill.yaml`
- 实验配置: `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml`

### 4. 运行实验
```bash
python src/run_experiment.py \
    --config_path "configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml"
```

## 配置文件位置

- **实验配置**: `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml`
- **组件配置**: `configs/components/`
  - LoRA模型: `language_models/huggingface_lora_language_model.yaml`
  - RL Agent: `agents/lora_rl_agent.yaml`
  - RL Callback: `callbacks/rl_training_callback.yaml`
  - Single-Skill Task: `tasks/db_bench_single_skill.yaml`

## 输出位置

```
outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/
├── config.yaml
├── runs.json
├── metric.json
└── callback_state/rl_training/
    └── lora_weights/  # 训练好的LoRA权重
```

## 详细文档

- 完整配置指南: `docs/RL_TRAINING_SETUP_QWEN25_7B.md`
- RL训练原理: `docs/RL_TRAINING_GUIDE.md`
- 实现总结: `IMPLEMENTATION_SUMMARY.md`

