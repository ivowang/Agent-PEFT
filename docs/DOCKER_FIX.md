# Docker MySQL 镜像问题修复说明

## 错误信息

```
docker.errors.ImageNotFound: 404 Client Error for http+docker://localhost/v1.47/containers/create?name=mysql_20295: Not Found ("No such image: mysql:latest")
docker.errors.APIError: 500 Server Error for http+docker://localhost/v1.47/images/create?tag=latest&fromImage=mysql: Internal Server Error
```

## 错误原因

1. Docker 找不到 `mysql:latest` 镜像
2. 尝试自动拉取镜像时出现网络错误（500 Server Error, EOF）

## 解决方案

### 1. 代码修改

**文件**: `src/tasks/instance/db_bench/container.py`

- 修改默认镜像名称为 `mysql:latest`（之前是 `mysql`）
- 添加镜像检查和自动拉取逻辑：
  - 如果镜像不存在，尝试自动拉取
  - 如果拉取失败，提供清晰的错误信息

### 2. 脚本修改

**文件**: `scripts/run_rl_training_qwen25_7b.sh`

- 添加了 Docker 和 MySQL 镜像检查步骤（Step 4）
- 检查 Docker daemon 是否运行
- 检查 MySQL 镜像是否存在（尝试多个可能的标签：`mysql:latest`, `mysql`, `mysql:8.0`, `mysql:8`）
- 如果镜像不存在，尝试自动拉取

## 使用方法

### 方法1: 手动拉取镜像（推荐）

在运行实验前，确保 MySQL 镜像已拉取：

```bash
docker pull mysql:latest
```

或者使用特定版本：

```bash
docker pull mysql:8.0
```

### 方法2: 自动拉取

脚本现在会自动检查并尝试拉取镜像。如果 Docker daemon 运行正常且有网络访问，会自动拉取。

### 方法3: 使用现有镜像

如果系统中已有其他 MySQL 镜像（如 `mysql:8.0`），可以修改代码中的默认镜像名称。

## 验证 Docker 环境

运行以下命令检查 Docker 环境：

```bash
# 检查 Docker daemon 是否运行
docker ps

# 检查 MySQL 镜像
docker images | grep mysql

# 如果镜像不存在，拉取镜像
docker pull mysql:latest
```

## 常见问题

### Q: Docker daemon 未运行
**A**: 启动 Docker daemon：
```bash
sudo systemctl start docker  # Linux
# 或
sudo service docker start    # 某些 Linux 发行版
```

### Q: 网络连接问题导致拉取失败
**A**: 
1. 检查网络连接
2. 配置 Docker 镜像加速器（如果在中国）
3. 手动拉取镜像后重试

### Q: 权限问题
**A**: 确保当前用户有 Docker 权限：
```bash
sudo usermod -aG docker $USER
# 然后重新登录或运行 newgrp docker
```

## 相关文件

- `src/tasks/instance/db_bench/container.py` - Docker 容器管理代码
- `scripts/run_rl_training_qwen25_7b.sh` - 实验运行脚本

