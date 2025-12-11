# RL Training with LoRA Guide

本指南说明如何使用LoRA + RL训练方式替代经验回放方法。

## 概述

新的实现使用：
1. **LoRA (Low-Rank Adaptation)**: 在基础LLM上添加可训练的LoRA模块（zero-init）
2. **Reinforcement Learning**: 基于任务执行结果的reward信号更新LoRA参数
3. **Single-Skill Tasks**: 每次随机生成单一技能的task，用于训练

## 组件说明

### 1. HuggingfaceLoRALanguageModel
- 位置: `src/language_models/instance/huggingface_lora_language_model.py`
- 功能: 支持LoRA的语言模型，zero-init初始化
- 关键方法:
  - `_inference_with_logprobs()`: 推理并返回logprobs用于RL训练
  - `save_lora()`: 保存LoRA权重
  - `train_mode()` / `eval_mode()`: 切换训练/评估模式

### 2. LoRARLAgent
- 位置: `src/agents/instance/lora_rl_agent.py`
- 功能: 支持RL训练的Agent，记录logprobs
- 特点: 与RLTrainingCallback配合使用

### 3. RLTrainingCallback
- 位置: `src/callbacks/instance/rl_training_callback.py`
- 功能: 实现REINFORCE算法，根据reward更新LoRA参数
- Reward设计:
  - 成功完成: +1.0
  - 答案错误: -0.1
  - 超时: -0.3

### 4. SingleSkillTaskGenerator
- 位置: `src/tasks/instance/db_bench/single_skill_task_generator.py`
- 功能: 从现有数据中筛选single-skill tasks，支持随机生成

### 5. DBBenchSingleSkill
- 位置: `src/tasks/instance/db_bench/task_single_skill.py`
- 功能: DBBench的变体，每次reset时动态生成新的single-skill task

## 配置示例

### 1. 准备Single-Skill数据

首先需要从现有数据中提取single-skill tasks：

```python
from src.tasks.instance.db_bench.single_skill_task_generator import SingleSkillTaskGenerator

# 从现有数据文件加载single-skill tasks
generator = SingleSkillTaskGenerator.load_from_existing_data(
    data_file_path="path/to/your/db_bench_data.json"
)

# 查看可用技能
print(generator.get_available_skills())
```

### 2. 配置文件示例

创建配置文件 `configs/assignments/rl_training_example.yaml`:

```yaml
assignment_config:
  task:
    name: "db_bench_single_skill"
    module: "src.tasks.instance.db_bench.task_single_skill"
    parameters:
      single_skill_task_generator:
        module: "src.tasks.instance.db_bench.single_skill_task_generator"
        parameters:
          skill_to_tasks_path: "path/to/single_skill_tasks.json"
      max_round: 10
      random_seed: 42
  
  agent:
    name: "lora_rl_agent"
    module: "src.agents.instance.lora_rl_agent"
    parameters:
      language_model: "lora_model"
      system_prompt: "You are a helpful SQL assistant."
  
  language_model_list:
    - name: "lora_model"
      module: "src.language_models.instance.huggingface_lora_language_model"
      parameters:
        model_name_or_path: "meta-llama/Llama-3.1-8B-Instruct"
        role_dict:
          USER: "user"
          AGENT: "assistant"
        lora_config:
          r: 16
          lora_alpha: 32
          target_modules: ["q_proj", "v_proj", "k_proj", "o_proj"]
          lora_dropout: 0.1
          bias: "none"
          task_type: "CAUSAL_LM"
  
  callback_dict:
    rl_training:
      name: "rl_training"
      module: "src.callbacks.instance.rl_training_callback"
      parameters:
        reward_weight: 1.0
        learning_rate: 1e-5
        optimizer_class: "AdamW"
        gradient_accumulation_steps: 1
        reward_correct: 1.0
        reward_incorrect: -0.1
        reward_timeout: -0.3
  
  output_dir: "outputs/rl_training/{TIMESTAMP}"
  sample_order: "default"
```

## 使用方法

### 运行训练

```bash
python ./src/run_experiment.py --config_path "configs/assignments/rl_training_example.yaml"
```

### 训练过程

1. **任务生成**: 每次reset时，`DBBenchSingleSkill`会随机选择一个skill，生成对应的task
2. **Agent推理**: `LoRARLAgent`使用LoRA模型进行推理，记录logprobs
3. **任务执行**: Task执行Agent的action，返回结果
4. **Reward计算**: `RLTrainingCallback`根据执行结果计算reward
5. **参数更新**: 使用REINFORCE算法更新LoRA参数

### 状态保存

训练状态会自动保存到：
- LoRA权重: `output_dir/callback_state/rl_training/lora_weights/`
- Optimizer状态: `output_dir/callback_state/rl_training/optimizer_state.pt`
- 训练步数: `output_dir/callback_state/rl_training/training_step.json`

### 恢复训练

如果训练中断，系统会自动恢复：
- LoRA权重会自动加载
- Optimizer状态会恢复
- 训练步数会继续

## 关键设计决策

### 1. Zero-Init LoRA
- LoRA权重初始化为零，确保初始时不影响基础模型性能
- 避免random init导致的性能下降

### 2. Single-Skill Tasks
- 每次只训练一个技能，简化学习目标
- 所有技能共享同一个LoRA模块，实现知识迁移

### 3. Reward设计
- 成功给予正reward (+1.0)
- 失败给予小负reward (-0.1)，避免过度惩罚
- 超时给予中等负reward (-0.3)

### 4. Gradient Accumulation
- 支持梯度累积，提高训练稳定性
- 默认accumulation_steps=1（每个样本后更新）

## 注意事项

1. **内存使用**: LoRA训练需要额外的GPU内存，建议使用gradient checkpointing
2. **学习率**: 建议从1e-5开始，根据训练效果调整
3. **Reward设计**: 可以根据任务特点调整reward值
4. **数据质量**: 确保single-skill tasks的质量，避免噪声数据

## 与经验回放的对比

| 特性 | 经验回放 | LoRA + RL |
|------|---------|-----------|
| 学习方式 | In-context learning | 参数更新 |
| 内存占用 | Prompt长度增长 | 固定LoRA参数 |
| 可学习模式 | 有限（受context限制） | 更复杂模式 |
| 推理效率 | 随历史增长下降 | 稳定 |
| 实现复杂度 | 低 | 中等 |

## 故障排除

### 问题1: LoRA初始化失败
- 检查PEFT版本: `pip install peft>=0.10.0`
- 确认模型支持LoRA

### 问题2: Reward不更新
- 检查RLTrainingCallback是否正确连接
- 确认logprobs是否正确记录

### 问题3: 训练不稳定
- 降低learning_rate
- 增加gradient_accumulation_steps
- 调整reward值

