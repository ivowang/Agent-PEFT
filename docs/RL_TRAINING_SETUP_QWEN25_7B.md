# Qwen2.5-7B-Instruct RL训练实验配置指南

本指南详细说明如何在Qwen2.5-7B-Instruct模型上配置和运行DB bench环境的RL训练实验。

## 前置要求

1. **Python环境**: Python 3.8+
2. **依赖库**: 
   - `peft>=0.10.0` (已添加到requirements.txt)
   - 其他依赖见 `requirements.txt`
3. **模型路径**: Qwen2.5-7B-Instruct模型已下载到指定路径
4. **数据文件**: DB benchmark数据文件存在

## 配置步骤

### 步骤1: 安装依赖

```bash
# 进入项目目录
cd /root/LifelongAgentBench

# 安装依赖（如果还没有安装）
pip install -r requirements.txt

# 确认PEFT已安装
python -c "import peft; print(peft.__version__)"
```

### 步骤2: 准备Single-Skill数据

从现有的DB benchmark数据中提取single-skill tasks：

```bash
# 使用数据准备脚本
python scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./data/v0303/db_bench/processed/v0317_first500/single_skill_tasks.json" \
    --min_tasks_per_skill 1
```

**说明**:
- `--input_data_path`: 输入的DB benchmark数据文件路径
- `--output_path`: 输出的single-skill tasks文件路径
- `--min_tasks_per_skill`: 每个skill最少需要的task数量（默认1）

**输出**: 脚本会显示：
- 找到的skill数量
- 每个skill的task数量
- 过滤后的统计信息

### 步骤3: 检查配置文件

配置文件已创建在：
```
configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml
```

**关键配置项说明**:

1. **Task配置** (`db_bench_single_skill`):
   - `single_skill_task_generator.skill_to_tasks_path`: single-skill数据文件路径
   - `max_round`: 最大交互轮数（默认3）

2. **Agent配置** (`lora_rl_agent`):
   - `language_model`: 使用 `Qwen2.5-7B-Instruct-LoRA`
   - `inference_config_dict`: 推理参数（greedy decoding）

3. **Language Model配置** (`Qwen2.5-7B-Instruct-LoRA`):
   - `model_name_or_path`: 模型路径（在`huggingface_lora_language_model.yaml`中配置）
   - `lora_config`: LoRA配置
     - `r`: LoRA rank（默认16）
     - `lora_alpha`: LoRA alpha（默认32）
     - `target_modules`: 目标模块（默认["q_proj", "v_proj", "k_proj", "o_proj"]）

4. **RL Callback配置** (`rl_training_callback`):
   - `reward_weight`: Reward权重（默认1.0）
   - `learning_rate`: 学习率（默认1e-5）
   - `optimizer_class`: 优化器（默认"AdamW"）
   - `reward_correct`: 成功reward（默认1.0）
   - `reward_incorrect`: 失败reward（默认-0.1）
   - `reward_timeout`: 超时reward（默认-0.3）

### 步骤4: 修改模型路径（如需要）

如果模型路径与默认配置不同，需要修改：
```
configs/components/language_models/huggingface_lora_language_model.yaml
```

找到 `Qwen2.5-7B-Instruct-LoRA` 部分，修改 `model_name_or_path`:

```yaml
Qwen2.5-7B-Instruct-LoRA:
  parameters:
    model_name_or_path: "/your/path/to/Qwen2.5-7B-Instruct"
```

### 步骤5: 修改数据路径（如需要）

如果数据文件路径不同，需要修改：
```
configs/components/tasks/db_bench_single_skill.yaml
```

修改 `single_skill_task_generator.skill_to_tasks_path`:

```yaml
single_skill_task_generator:
  parameters:
    skill_to_tasks_path: "./your/path/to/single_skill_tasks.json"
```

### 步骤6: 配置实验参数（可选）

在 `rl_training.yaml` 中可以调整：

1. **样本数量**: 修改 `sample_order` 列表，或使用 `"default"` 运行所有任务
2. **输出目录**: 修改 `output_dir` 路径
3. **环境配置**: `use_task_client_flag` 设置为 `false`（本地运行）

## 运行实验

### 方法1: 使用自动化脚本（推荐）

```bash
# 使用提供的bash脚本（会自动检查依赖、准备数据、运行实验）
bash scripts/run_rl_training_qwen25_7b.sh
```

脚本会自动：
1. 检查数据文件是否存在
2. 准备single-skill数据（如果不存在）
3. 检查配置文件
4. 检查Python依赖
5. 运行实验

### 方法2: 手动运行

```bash
# 1. 准备数据（如果还没有）
python scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./data/v0303/db_bench/processed/v0317_first500/single_skill_tasks.json"

# 2. 运行实验
python src/run_experiment.py \
    --config_path "configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml"
```

## 实验输出

实验输出会保存在：
```
outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/
```

目录结构：
```
outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/
├── config.yaml                    # 实验配置
├── runs.json                      # 会话记录
├── metric.json                    # 评估指标
├── exception.txt                  # 异常记录
├── singleton_logger.log           # 日志文件
└── callback_state/
    └── rl_training/
        ├── lora_weights/          # LoRA权重（可恢复训练）
        ├── optimizer_state.pt    # Optimizer状态
        └── training_step.json     # 训练步数
```

## 监控训练过程

### 查看日志

```bash
# 实时查看日志
tail -f outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/singleton_logger.log

# 查看RL训练相关信息
grep "RLTrainingCallback" outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/singleton_logger.log
```

### 检查训练状态

```bash
# 查看训练步数
cat outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/callback_state/rl_training/training_step.json

# 查看会话记录
cat outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}/runs.json | jq '.[] | {sample_index, evaluation_record, sample_status}'
```

## 恢复训练

如果训练中断，系统会自动恢复：
- LoRA权重会自动加载
- Optimizer状态会恢复
- 训练步数会继续

只需重新运行相同的命令即可。

## 调整超参数

### 学习率调整

在 `configs/components/callbacks/rl_training_callback.yaml` 中修改：

```yaml
rl_training_callback:
  parameters:
    learning_rate: 5e-6  # 降低学习率，更稳定
    # 或
    learning_rate: 2e-5   # 提高学习率，更快收敛
```

### Reward调整

```yaml
rl_training_callback:
  parameters:
    reward_correct: 2.0      # 增加成功reward
    reward_incorrect: -0.2   # 调整失败惩罚
    reward_timeout: -0.5     # 调整超时惩罚
```

### LoRA配置调整

在 `configs/components/language_models/huggingface_lora_language_model.yaml` 中修改：

```yaml
default:
  parameters:
    lora_config:
      r: 32              # 增加rank，更多参数
      lora_alpha: 64    # 相应增加alpha
      lora_dropout: 0.2 # 增加dropout，防止过拟合
```

## 故障排除

### 问题1: PEFT库未安装

```bash
pip install peft>=0.10.0
```

### 问题2: 模型路径错误

检查 `configs/components/language_models/huggingface_lora_language_model.yaml` 中的模型路径是否正确。

### 问题3: 数据文件不存在

确保：
1. 原始数据文件存在
2. 运行了数据准备脚本
3. single-skill数据文件路径正确

### 问题4: GPU内存不足

- 降低LoRA rank (`r`)
- 使用gradient checkpointing
- 减少batch size（如果支持）

### 问题5: 训练不稳定

- 降低学习率
- 增加gradient_accumulation_steps
- 调整reward值

## 实验建议

1. **小规模测试**: 先用少量样本（如10个）测试基本功能
2. **监控指标**: 关注成功率、平均reward等指标
3. **保存检查点**: 定期检查LoRA权重是否正确保存
4. **对比实验**: 可以对比不同超参数设置的效果

## 下一步

训练完成后，可以：
1. 分析 `metric.json` 中的评估指标
2. 查看 `runs.json` 中的详细会话记录
3. 使用训练好的LoRA权重进行推理
4. 进行消融实验，对比不同配置的效果

