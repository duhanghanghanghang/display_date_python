#!/bin/bash

###############################################################################
# Display Date 自动部署脚本
# 
# 功能：
# 1. 从 Git 拉取最新代码
# 2. 安装/更新依赖
# 3. 清理日志（如果超过限制）
# 4. 重启服务
#
# 使用场景：
# - 手动执行: bash auto_deploy.sh
# - GitHub Webhook 自动触发
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 开始部署
echo ""
echo "======================================"
log_info "开始自动部署"
echo "======================================"
echo ""

# 记录部署时间
DEPLOY_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log_info "部署时间: $DEPLOY_TIME"

# 获取脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
log_info "项目目录: $SCRIPT_DIR"

# 1. 拉取最新代码
echo ""
log_info "步骤 1/5: 拉取最新代码"
echo "--------------------------------------"

if [ ! -d ".git" ]; then
    log_error "当前目录不是 Git 仓库"
    exit 1
fi

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)
log_info "当前分支: $CURRENT_BRANCH"

# 保存本地修改（如果有）
if ! git diff-index --quiet HEAD --; then
    log_warning "检测到本地修改，将暂存..."
    git stash save "Auto-deploy stash at $DEPLOY_TIME"
    STASHED=true
else
    STASHED=false
fi

# 拉取最新代码
log_info "拉取最新代码..."
if git pull origin "$CURRENT_BRANCH"; then
    log_success "代码拉取成功"
else
    log_error "代码拉取失败"
    
    # 恢复暂存的修改
    if [ "$STASHED" = true ]; then
        git stash pop
    fi
    
    exit 1
fi

# 恢复暂存的修改
if [ "$STASHED" = true ]; then
    log_info "恢复本地修改..."
    if git stash pop; then
        log_success "本地修改已恢复"
    else
        log_warning "恢复本地修改时发生冲突，请手动解决"
    fi
fi

# 2. 更新依赖
echo ""
log_info "步骤 2/5: 更新依赖"
echo "--------------------------------------"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    log_warning "虚拟环境不存在，创建中..."
    python3 -m venv venv
    log_success "虚拟环境创建完成"
fi

# 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate

# 更新 pip
log_info "更新 pip..."
pip install --upgrade pip -q

# 安装/更新依赖
if [ -f "requirements.txt" ]; then
    log_info "安装依赖..."
    pip install -r requirements.txt -q
    log_success "依赖安装完成"
else
    log_warning "未找到 requirements.txt"
fi

# 3. 清理日志
echo ""
log_info "步骤 3/5: 数据库迁移"
echo "--------------------------------------"

# 运行数据库迁移
log_info "检查并执行数据库迁移..."
if alembic upgrade head; then
    log_success "数据库迁移完成"
else
    log_warning "数据库迁移失败（可能已是最新状态）"
fi

# 4. 清理日志
echo ""
log_info "步骤 4/5: 清理日志"
echo "--------------------------------------"

# 运行日志清理脚本
if python3 -c "
from app.logger import log_manager
log_manager.cleanup()
" 2>/dev/null; then
    log_success "日志清理完成"
else
    log_warning "日志清理失败（可能是首次运行）"
fi

# 4. 重启服务
echo ""
log_info "步骤 5/5: 重启服务"
echo "--------------------------------------"

# 检查是否使用 systemd 服务
if systemctl is-active --quiet display-date 2>/dev/null; then
    log_info "检测到 systemd 服务，重启中..."
    
    if sudo systemctl restart display-date; then
        log_success "服务重启成功"
        
        # 等待服务启动
        sleep 2
        
        # 检查服务状态
        if systemctl is-active --quiet display-date; then
            log_success "服务运行正常"
        else
            log_error "服务启动失败"
            log_info "查看日志: sudo journalctl -u display-date -n 50"
            exit 1
        fi
    else
        log_error "服务重启失败"
        exit 1
    fi
    
# 检查是否使用 Docker
elif docker ps | grep -q display-date 2>/dev/null; then
    log_info "检测到 Docker 容器，重启中..."
    
    if docker-compose restart 2>/dev/null || docker restart display-date 2>/dev/null; then
        log_success "Docker 容器重启成功"
    else
        log_error "Docker 容器重启失败"
        exit 1
    fi
    
# 检查是否有运行中的进程
elif pgrep -f "python.*run.py" > /dev/null; then
    log_info "检测到运行中的进程，重启中..."
    
    # 终止旧进程
    pkill -f "python.*run.py"
    sleep 2
    
    # 启动新进程（后台运行）
    nohup python3 run.py > logs/app.log 2>&1 &
    sleep 2
    
    if pgrep -f "python.*run.py" > /dev/null; then
        log_success "服务重启成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
else
    log_warning "未检测到运行中的服务"
    log_info "如需启动服务，请运行: python3 run.py"
    log_info "或配置 systemd 服务: sudo systemctl start display-date"
fi

# 完成
echo ""
echo "======================================"
log_success "自动部署完成！"
echo "======================================"
echo ""
log_info "部署摘要："
echo "  - 分支: $CURRENT_BRANCH"
echo "  - 最新提交: $(git log -1 --pretty=format:'%h - %s (%an, %ar)')"
echo "  - 部署时间: $DEPLOY_TIME"
echo ""

# 健康检查
log_info "执行健康检查..."
sleep 2

if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    log_success "API 服务运行正常"
    echo "  - 访问地址: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
else
    log_warning "无法连接到 API 服务（可能需要等待启动）"
fi

echo ""
