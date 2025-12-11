#!/bin/bash
# RL Training实验运行脚本
# 用于在qwen25_7b_instruct模型上运行DB bench的RL训练实验

set -e  # 遇到错误立即退出

# 配置变量
CONFIG_PATH="configs/assignments/experiments/qwen25_7b_instruct/instance/db_bench/instance/rl_training.yaml"
DATA_FILE_PATH="./data/v0303/db_bench/processed/v0317_first500/entry_dict.json"
SINGLE_SKILL_DATA_PATH="./data/v0303/db_bench/processed/v0317_first500/single_skill_tasks.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}RL Training Experiment Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# 步骤1: 检查数据文件是否存在
echo -e "\n${YELLOW}[Step 1] Checking data files...${NC}"
if [ ! -f "$DATA_FILE_PATH" ]; then
    echo -e "${RED}Error: Data file not found: $DATA_FILE_PATH${NC}"
    echo "Please ensure the DB benchmark data file exists."
    exit 1
fi
echo -e "${GREEN}✓ Data file found: $DATA_FILE_PATH${NC}"

# 步骤2: 准备single-skill数据
echo -e "\n${YELLOW}[Step 2] Preparing single-skill tasks...${NC}"
if [ ! -f "$SINGLE_SKILL_DATA_PATH" ]; then
    echo "Single-skill data not found. Generating..."
    python scripts/prepare_single_skill_data.py \
        --input_data_path "$DATA_FILE_PATH" \
        --output_path "$SINGLE_SKILL_DATA_PATH" \
        --min_tasks_per_skill 1
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to generate single-skill tasks${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Single-skill tasks generated: $SINGLE_SKILL_DATA_PATH${NC}"
else
    echo -e "${GREEN}✓ Single-skill data already exists: $SINGLE_SKILL_DATA_PATH${NC}"
fi

# 步骤3: 检查配置文件
echo -e "\n${YELLOW}[Step 3] Checking configuration file...${NC}"
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${RED}Error: Config file not found: $CONFIG_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Config file found: $CONFIG_PATH${NC}"

# 步骤4: 检查Python依赖
echo -e "\n${YELLOW}[Step 4] Checking Python dependencies...${NC}"
python -c "import peft" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: PEFT library not installed${NC}"
    echo "Please install it with: pip install peft>=0.10.0"
    exit 1
fi
echo -e "${GREEN}✓ PEFT library found${NC}"

# 步骤5: 运行实验
echo -e "\n${YELLOW}[Step 5] Starting RL training experiment...${NC}"
echo -e "${GREEN}Config: $CONFIG_PATH${NC}"
echo -e "${GREEN}Output will be saved to: outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}${NC}"
echo ""

python src/run_experiment.py --config_path "$CONFIG_PATH"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Experiment completed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}Experiment failed!${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

