# LoRA + RL 实现总结

## 实现概述

本次修改实现了使用PEFT (LoRA) + Reinforcement Learning替代经验回放的方法，用于DB环境下的Agent进化。

## 新增文件

### 1. Language Models
- `src/language_models/instance/huggingface_lora_language_model.py`
  - HuggingfaceLoRALanguageModel类
  - 支持zero-init LoRA
  - 提供`_inference_with_logprobs()`方法用于RL训练

### 2. Agents
- `src/agents/instance/lora_rl_agent.py`
  - LoRARLAgent类
  - 与RLTrainingCallback配合记录logprobs

### 3. Callbacks
- `src/callbacks/instance/rl_training_callback.py`
  - RLTrainingCallback类
  - 实现REINFORCE算法
  - 根据reward更新LoRA参数

### 4. Tasks
- `src/tasks/instance/db_bench/single_skill_task_generator.py`
  - SingleSkillTaskGenerator类
  - 从现有数据中筛选single-skill tasks
  - 支持随机生成任务

- `src/tasks/instance/db_bench/task_single_skill.py`
  - DBBenchSingleSkill类
  - DBBench的变体，支持动态生成single-skill tasks

### 5. Documentation
- `docs/RL_TRAINING_GUIDE.md`
  - 详细的使用指南和配置示例

## 修改的文件

### 1. Dependencies
- `requirements.txt`
  - 添加 `peft~=0.10.0`

### 2. Module Exports
- `src/language_models/instance/__init__.py`
  - 导出HuggingfaceLoRALanguageModel

- `src/agents/instance/__init__.py`
  - 导出LoRARLAgent

- `src/callbacks/instance/__init__.py`
  - 导出RLTrainingCallback

- `src/tasks/instance/db_bench/__init__.py`
  - 导出DBBenchSingleSkill和SingleSkillTaskGenerator

### 3. Callback Constructor
- `src/callbacks/constructor.py`
  - 添加RLTrainingCallback的处理逻辑
  - 自动连接LoRARLAgent和RLTrainingCallback

## 核心功能

### 1. Zero-Init LoRA
- LoRA权重初始化为零，确保初始时不影响基础模型
- 使用PEFT库的默认zero-init机制

### 2. Single-Skill Task Generation
- 从现有数据中筛选只包含单一技能的tasks
- 每次reset时随机选择一个skill，生成对应的task
- 所有skill共享同一个LoRA模块

### 3. RL Training
- 使用REINFORCE算法
- Reward设计:
  - 成功: +1.0
  - 错误: -0.1
  - 超时: -0.3
- 支持梯度累积

### 4. State Management
- 自动保存/恢复LoRA权重
- 保存optimizer状态
- 记录训练步数

## 使用流程

1. **准备数据**: 使用SingleSkillTaskGenerator从现有数据中提取single-skill tasks
2. **配置**: 创建配置文件，指定LoRA模型、Agent、Callback等
3. **训练**: 运行`run_experiment.py`，系统会自动:
   - 每次reset生成新的single-skill task
   - Agent推理并记录logprobs
   - 根据执行结果计算reward
   - 更新LoRA参数

## 关键设计决策

1. **Zero-Init LoRA**: 避免random init导致的性能下降
2. **Single-Skill Tasks**: 简化学习目标，每次只学习一个技能
3. **Shared LoRA**: 所有skill共享LoRA模块，实现知识迁移
4. **REINFORCE算法**: 简单有效的RL算法，适合在线学习

## 注意事项

1. 需要安装PEFT库: `pip install peft>=0.10.0`
2. LoRA训练需要额外的GPU内存
3. 建议从较小的learning_rate开始（1e-5）
4. 可以根据任务特点调整reward值

## 测试建议

1. 使用小规模数据测试基本功能
2. 验证LoRA权重正确保存/加载
3. 检查reward计算是否正确
4. 观察训练过程中的loss变化

## 后续改进方向

1. 支持更复杂的RL算法（PPO, A2C等）
2. 支持multi-skill tasks的渐进式训练
3. 添加更多的reward shaping策略
4. 支持分布式训练

