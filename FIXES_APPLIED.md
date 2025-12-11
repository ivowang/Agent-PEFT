# 代码修复说明

## 修复的问题

### 问题1: 模块导入错误
**错误信息**: `ModuleNotFoundError: No module named 'src'`

**原因**: `prepare_single_skill_data.py` 脚本在导入时无法找到 `src` 模块，因为Python路径未正确设置。

**解决方案**:
1. 在脚本开头添加路径设置代码：
   ```python
   script_dir = Path(__file__).parent
   project_root = script_dir.parent.resolve()
   if str(project_root) not in sys.path:
       sys.path.insert(0, str(project_root))
   ```

2. 简化脚本逻辑，避免复杂的模块依赖：
   - 移除了对 `SingleSkillTaskGenerator` 类的直接导入
   - 直接在脚本中实现核心逻辑（加载、筛选、保存）

3. 在bash脚本中设置PYTHONPATH：
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

### 问题2: Python命令路径
**解决方案**: 将所有 `python` 命令改为 `python3`，确保使用正确的Python解释器。

## 修复的文件

1. **scripts/prepare_single_skill_data.py**
   - 添加了路径设置逻辑
   - 简化了实现，避免复杂依赖
   - 直接实现single-skill task筛选逻辑

2. **scripts/run_rl_training_qwen25_7b.sh**
   - 添加了PYTHONPATH设置
   - 将所有python命令改为python3
   - 确保在运行实验前设置正确的环境变量

## 验证结果

✅ `prepare_single_skill_data.py` 可以正常运行
✅ 成功生成 `single_skill_tasks.json`
✅ 数据格式正确，包含5个skills，10个tasks

## 现在可以运行

```bash
cd /root/Agent-PEFT
bash scripts/run_rl_training_qwen25_7b.sh
```

脚本现在应该可以：
1. ✅ 自动创建测试数据（如果不存在）
2. ✅ 自动生成single-skill数据（如果不存在）
3. ✅ 正确设置Python路径
4. ✅ 运行RL训练实验

## 测试命令

```bash
# 测试数据准备脚本
cd /root/Agent-PEFT
python3 scripts/prepare_single_skill_data.py \
    --input_data_path "./data/v0303/db_bench/processed/v0317_first500/entry_dict.json" \
    --output_path "./test_output.json" \
    --min_tasks_per_skill 1

# 验证生成的数据
python3 -c "
import json
data = json.load(open('test_output.json'))
print(f'Skills: {list(data.keys())}')
print(f'Total tasks: {sum(len(v) for v in data.values())}')
"
```

