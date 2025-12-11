# Qwen2.5-7B-Instruct RL训练配置总结

## 已创建的配置文件

### 1. 组件配置文件

#### Language Models
- `configs/components/language_models/huggingface_lora_language_model.yaml`
  - 定义LoRA语言模型配置
  - 包含Qwen2.5-7B-Instruct-LoRA的配置

#### Agents
- `configs/components/agents/lora_rl_agent.yaml`
  - 定义LoRA RL Agent配置

#### Callbacks
- `configs/components/callbacks/rl_training_callback.yaml`
  - 定义RL训练回调配置
  - 包含reward、learning_rate等超参数

#### Tasks
- `configs/components/tasks/db_bench_single_skill.yaml`
  - 定义single-skill task配置
  - 包含数据路径和任务参数

### 2. 实验配置文件

- `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml`
  - 完整的实验配置
  - 整合所有组件
  - 指定输出目录和样本顺序

### 3. 全局配置更新

- `configs/definition.yaml`
  - 添加了新组件的导入路径

## 已创建的脚本

### 1. 数据准备脚本
- `scripts/prepare_single_skill_data.py`
  - 从现有数据中提取single-skill tasks
  - 支持过滤和统计

### 2. 实验运行脚本
- `scripts/run_rl_training_qwen25_7b.sh`
  - 自动化实验运行脚本
  - 包含依赖检查、数据准备、实验运行

## 配置步骤清单

### ✅ 步骤1: 安装依赖
```bash
pip install -r requirements.txt
```

### ✅ 步骤2: 准备Single-Skill数据
```bash
python scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./data/v0303/db_bench/processed/v0317_first500/single_skill_tasks.json"
```

### ✅ 步骤3: 检查/修改配置（如需要）

**模型路径** (如需要):
- 文件: `configs/components/language_models/huggingface_lora_language_model.yaml`
- 修改: `Qwen2.5-7B-Instruct-LoRA.parameters.model_name_or_path`

**数据路径** (如需要):
- 文件: `configs/components/tasks/db_bench_single_skill.yaml`
- 修改: `single_skill_task_generator.parameters.skill_to_tasks_path`

**实验参数** (可选):
- 文件: `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml`
- 可调整: `sample_order`, `output_dir`等

### ✅ 步骤4: 运行实验

**方法1: 使用自动化脚本**
```bash
bash scripts/run_rl_training_qwen25_7b.sh
```

**方法2: 手动运行**
```bash
python src/run_experiment.py \
    --config_path "configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml"
```

## 关键配置项说明

### LoRA配置
- **r**: 16 (LoRA rank)
- **lora_alpha**: 32
- **target_modules**: ["q_proj", "v_proj", "k_proj", "o_proj"]
- **lora_dropout**: 0.1

### RL训练配置
- **learning_rate**: 1e-5
- **optimizer**: AdamW
- **reward_correct**: 1.0
- **reward_incorrect**: -0.1
- **reward_timeout**: -0.3

### 任务配置
- **max_round**: 3
- **task_type**: single-skill (动态生成)

## 文件结构

```
LifelongAgentBench/
├── configs/
│   ├── components/
│   │   ├── language_models/
│   │   │   └── huggingface_lora_language_model.yaml  ✨ NEW
│   │   ├── agents/
│   │   │   └── lora_rl_agent.yaml  ✨ NEW
│   │   ├── callbacks/
│   │   │   └── rl_training_callback.yaml  ✨ NEW
│   │   └── tasks/
│   │       └── db_bench_single_skill.yaml  ✨ NEW
│   ├── assignments/
│   │   └── experiments/
│   │       └── qwen25_7b_instruct/
│   │           └── instance/
│   │               └── db_bench/
│   │                   └── instance/
│   │                       └── rl_training.yaml  ✨ NEW
│   └── definition.yaml  ✏️ MODIFIED
├── scripts/
│   ├── prepare_single_skill_data.py  ✨ NEW
│   └── run_rl_training_qwen25_7b.sh  ✨ NEW
└── docs/
    ├── RL_TRAINING_SETUP_QWEN25_7B.md  ✨ NEW
    └── RL_TRAINING_GUIDE.md  ✨ NEW
```

## 验证清单

运行实验前，请确认：

- [ ] PEFT库已安装 (`pip install peft>=0.10.0`)
- [ ] 模型路径正确
- [ ] 数据文件存在
- [ ] Single-skill数据已生成
- [ ] 配置文件路径正确
- [ ] GPU内存充足

## 快速测试

```bash
# 1. 测试数据准备
python scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./test_single_skill.json" \
    --min_tasks_per_skill 1

# 2. 测试配置加载
python -c "
from src.utils import ConfigLoader
config = ConfigLoader().load_from('configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml')
print('Config loaded successfully!')
print('Task:', config['assignment_config']['task'])
print('Agent:', config['assignment_config']['agent']['name'])
"
```

## 下一步

1. 运行实验: `bash scripts/run_rl_training_qwen25_7b.sh`
2. 监控训练: 查看日志文件
3. 分析结果: 检查 `metric.json` 和 `runs.json`
4. 调整超参数: 根据结果优化配置

## 支持文档

- **快速开始**: `QUICKSTART_RL_TRAINING.md`
- **详细配置**: `docs/RL_TRAINING_SETUP_QWEN25_7B.md`
- **原理说明**: `docs/RL_TRAINING_GUIDE.md`
- **实现细节**: `IMPLEMENTATION_SUMMARY.md`

