#!/bin/bash
# RL Training实验运行脚本
# 用于在qwen25_7b_instruct模型上运行DB bench的RL训练实验

# set -e  # 注释掉，允许在数据不存在时创建数据

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

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
    echo -e "${YELLOW}Warning: Data file not found: $DATA_FILE_PATH${NC}"
    echo -e "${YELLOW}Creating minimal test data...${NC}"
    
    # 创建最小测试数据
    python3 scripts/create_minimal_test_data.py \
        --output_path "$DATA_FILE_PATH" \
        --num_samples 10
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create test data${NC}"
        echo -e "${YELLOW}Please ensure the DB benchmark data file exists or run:${NC}"
        echo "  python scripts/create_minimal_test_data.py --output_path \"$DATA_FILE_PATH\""
        exit 1
    fi
    echo -e "${GREEN}✓ Created minimal test data: $DATA_FILE_PATH${NC}"
    echo -e "${YELLOW}Note: This is a minimal test dataset. For full experiments, please generate data using the data factory.${NC}"
else
    echo -e "${GREEN}✓ Data file found: $DATA_FILE_PATH${NC}"
fi

# 步骤2: 准备single-skill数据
echo -e "\n${YELLOW}[Step 2] Preparing single-skill tasks...${NC}"
if [ ! -f "$SINGLE_SKILL_DATA_PATH" ]; then
    echo "Single-skill data not found. Generating..."
    python3 scripts/prepare_single_skill_data.py \
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

# 步骤4: 检查Docker和MySQL镜像
echo -e "\n${YELLOW}[Step 4] Checking Docker and MySQL image...${NC}"
python3 -c "
import docker
try:
    client = docker.from_env()
    # Test Docker connection
    client.ping()
    print('✓ Docker daemon is running')
    
    # Check for mysql image (try different tags)
    mysql_images = ['mysql:latest', 'mysql', 'mysql:8.0', 'mysql:8']
    found_image = None
    for img_name in mysql_images:
        try:
            client.images.get(img_name)
            found_image = img_name
            print(f'✓ Found MySQL image: {img_name}')
            break
        except docker.errors.ImageNotFound:
            continue
    
    if not found_image:
        print('⚠ MySQL image not found. Attempting to pull mysql:latest...')
        try:
            client.images.pull('mysql:latest')
            print('✓ Successfully pulled mysql:latest')
        except Exception as e:
            print(f'✗ Failed to pull mysql:latest: {e}')
            print('Please ensure Docker is running and you have network access.')
            print('Or manually pull the image with: docker pull mysql:latest')
            exit(1)
except docker.errors.DockerException as e:
    print(f'✗ Docker error: {e}')
    print('Please ensure Docker is installed and the daemon is running.')
    exit(1)
except Exception as e:
    print(f'✗ Unexpected error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker check failed${NC}"
    exit 1
fi

# 步骤5: 检查Python依赖
echo -e "\n${YELLOW}[Step 5] Checking Python dependencies...${NC}"
python3 -c "import peft" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: PEFT library not installed${NC}"
    echo "Please install it with: pip install peft>=0.10.0"
    exit 1
fi
echo -e "${GREEN}✓ PEFT library found${NC}"

# 步骤6: 运行实验
echo -e "\n${YELLOW}[Step 6] Starting RL training experiment...${NC}"
echo -e "${GREEN}Config: $CONFIG_PATH${NC}"
echo -e "${GREEN}Output will be saved to: outputs/rl_training/qwen25_7b_instruct/db_bench/{TIMESTAMP}${NC}"
echo ""

# 确保PYTHONPATH已设置
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 src/run_experiment.py --config_path "$CONFIG_PATH"

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

