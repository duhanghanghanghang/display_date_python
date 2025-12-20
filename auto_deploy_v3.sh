#!/bin/bash
# 自动部署脚本 v3.0 - 强制kill版本
# 功能：强制杀死进程 + 健康检查 + 完整日志

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
APP_DIR="/srv/app/display_date_python"
SERVICE_NAME="display-date"
VENV_PATH="$APP_DIR/venv"
PORT=8000
MAX_WAIT=30

# 日志函数
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
separator() { echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; }

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    error "请使用 root 权限运行"
    exit 1
fi

separator
success "自动部署开始！"
separator
echo ""

# ============ 步骤 1/5: 拉取代码 ============
info "步骤 1/5: 拉取最新代码"
separator
cd "$APP_DIR" || exit 1

CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
info "当前版本: $CURRENT_COMMIT"

git fetch origin master
git pull origin master

NEW_COMMIT=$(git rev-parse --short HEAD)
info "新版本: $NEW_COMMIT"

[ "$CURRENT_COMMIT" = "$NEW_COMMIT" ] && warning "代码无更新" || success "代码更新成功"
echo ""

# ============ 步骤 2/5: 安装依赖 ============
info "步骤 2/5: 安装依赖"
separator

if [ -f "requirements.txt" ] && [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    pip install -r requirements.txt --quiet
    success "依赖安装完成"
else
    warning "跳过依赖安装"
fi
echo ""

# ============ 步骤 3/5: 清理日志 ============
info "步骤 3/5: 清理日志"
separator

if [ -d "logs" ]; then
    LOG_SIZE=$(du -sh logs 2>/dev/null | cut -f1)
    info "日志大小: $LOG_SIZE"
    find logs -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    success "日志清理完成"
fi
echo ""

# ============ 步骤 4/5: 强制重启服务 ============
info "步骤 4/5: 强制重启服务"
separator

# 4.1 停止systemd服务
if systemctl is-active --quiet $SERVICE_NAME; then
    info "停止 systemd 服务..."
    systemctl stop $SERVICE_NAME
    sleep 2
fi

# 4.2 强制kill所有相关进程
info "清理残留进程..."
ps aux | grep "$APP_DIR" | grep python | grep -v grep | awk '{print $2}' | while read pid; do
    [ -n "$pid" ] && kill -9 $pid 2>/dev/null && info "已终止进程: $pid"
done

# 4.3 释放端口
if lsof -ti:$PORT > /dev/null 2>&1; then
    warning "端口 $PORT 被占用，正在释放..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
fi

sleep 2

# 4.4 启动服务
info "启动服务..."
systemctl start $SERVICE_NAME

# 4.5 等待启动
WAIT=0
while [ $WAIT -lt $MAX_WAIT ]; do
    if systemctl is-active --quiet $SERVICE_NAME; then
        success "服务启动成功"
        break
    fi
    WAIT=$((WAIT + 1))
    echo -n "."
    sleep 1
done
echo ""

if [ $WAIT -ge $MAX_WAIT ]; then
    error "服务启动超时"
    systemctl status $SERVICE_NAME --no-pager -l
    exit 1
fi

echo ""

# ============ 步骤 5/5: 健康检查 ============
info "步骤 5/5: 健康检查"
separator

# 检查进程
if pgrep -f "uvicorn.*$APP_DIR" > /dev/null; then
    success "✓ 进程运行正常"
else
    error "✗ 进程未找到"
fi

# 检查端口
if netstat -tuln 2>/dev/null | grep ":$PORT " > /dev/null; then
    success "✓ 端口 $PORT 正在监听"
else
    error "✗ 端口 $PORT 未监听"
fi

# API健康检查
TRIES=0
while [ $TRIES -lt 10 ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        success "✓ API 响应正常 (HTTP $HTTP_CODE)"
        break
    fi
    TRIES=$((TRIES + 1))
    [ $TRIES -lt 10 ] && echo -n "." && sleep 1
done
echo ""

[ $TRIES -ge 10 ] && warning "API 可能需要更多时间启动"

echo ""

# ============ 部署摘要 ============
separator
success "自动部署完成！"
separator
echo ""

info "部署摘要:"
echo "  - 分支: master"
echo "  - 最新提交: $NEW_COMMIT ($(git log -1 --pretty=format:'%an, %ar'))"
echo "  - 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

info "服务状态:"
systemctl status $SERVICE_NAME --no-pager -l | head -8
echo ""

info "查看日志:"
echo "  实时日志: journalctl -u $SERVICE_NAME -f"
echo "  应用日志: tail -f $APP_DIR/logs/app.log"
echo ""

separator
