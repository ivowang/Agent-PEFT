# 错误解释：AssertionError in _get_custom_instance_info_dict

## 错误信息

```
File "/root/Agent-PEFT/src/run_experiment.py", line 142, in _get_custom_instance_info_dict
    assert parameter_name in default_parameters  # Do not remove this assertion.
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

## 错误原因

这个错误发生在配置验证阶段。系统检查 `custom_parameters` 中的每个参数是否都在 `default_parameters` 中存在。

### 问题根源

`rl_training.yaml` 配置文件导入了 `../../../agent.yaml`，这个文件定义了：

```yaml
assignment_config:
  agent:
    name: language_model_agent
    custom_parameters:
      language_model: Qwen2.5-7B-Instruct
      inference_config_dict:
        ...
```

当配置合并时：
1. `agent.yaml` 的 `custom_parameters` 被加载
2. `rl_training.yaml` 的 `custom_parameters` 会覆盖它
3. 但是，如果合并后的 `custom_parameters` 中有参数不在 `lora_rl_agent.yaml` 的 `default_parameters` 中，就会报错

### 配置验证逻辑

在 `src/run_experiment.py` 的 `_get_custom_instance_info_dict` 方法中：

```python
default_parameters = default_instance_info_dict.get("parameters") or {}
custom_parameters = custom_instance_info_dict.get("custom_parameters") or {}
for parameter_name, custom_parameter_value in custom_parameters.items():
    assert parameter_name in default_parameters  # 这里报错
    default_parameters[parameter_name] = custom_parameter_value
```

这个断言确保：
- `custom_parameters` 中的每个参数名都必须在 `default_parameters` 中存在
- 这样可以防止配置错误，确保只覆盖已定义的参数

## 解决方案

### 方案1: 移除冲突的导入（已应用）

从 `rl_training.yaml` 中移除 `../../../agent.yaml` 的导入：

```yaml
import:
  - ../task.yaml
  # - ../../../agent.yaml  # 移除这行
  - ../../../../../../definition.yaml
```

这样就不会有配置冲突了。

### 方案2: 确保所有参数都在default_parameters中

确保 `lora_rl_agent.yaml` 的 `parameters` 中包含所有可能用到的参数：

```yaml
lora_rl_agent:
  module: "src.agents.instance.lora_rl_agent.LoRARLAgent"
  parameters:
    language_model: null  # ✅ 已添加
    be replaced by custom_parameters
    system_prompt: "You are a helpful SQL assistant."
    inference_config_dict: {}  # ✅ 已存在
    rl_callback: null  # ✅ 已添加
```

## 修复状态

✅ **已修复**: 
1. 移除了 `agent.yaml` 的导入
2. 确保 `lora_rl_agent.yaml` 包含所有必需的参数

## 验证

修复后，配置应该可以正常加载。可以运行：

```bash
cd /root/Agent-PEFT
bash scripts/run_rl_training_qwen25_7b.sh
```

## 相关文件

- `configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml` - 实验配置
- `configs/components/agents/lora_rl_agent.yaml` - Agent组件配置
- `src/run_experiment.py` - 配置验证逻辑

