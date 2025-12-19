#!/bin/bash

###############################################################################
# 快速修复脚本 - 修复服务器数据库缺失字段
# 
# 使用方法：
#   在服务器上运行: bash fix_database.sh
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}======================================"
echo "数据库修复脚本"
echo -e "======================================${NC}"
echo ""

# 检查是否在项目根目录
if [ ! -f "alembic.ini" ]; then
    echo -e "${RED}错误：请在项目根目录运行此脚本${NC}"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}错误：虚拟环境不存在${NC}"
    echo "请先运行: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 检查 Alembic 是否安装
if ! python3 -c "import alembic" 2>/dev/null; then
    echo -e "${YELLOW}安装 Alembic...${NC}"
    pip install alembic==1.13.1 -q
    echo -e "${GREEN}✓ Alembic 安装完成${NC}"
fi

# 备份数据库（可选）
echo ""
read -p "是否备份数据库？[Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${YELLOW}备份数据库到 $BACKUP_FILE...${NC}"
    
    # 从 .env 读取数据库配置
    DB_HOST=$(grep DATABASE_URL .env | cut -d@ -f2 | cut -d: -f1)
    DB_USER=$(grep DATABASE_URL .env | cut -d/ -f3 | cut -d: -f1)
    DB_PASS=$(grep DATABASE_URL .env | cut -d: -f3 | cut -d@ -f1)
    DB_NAME=$(grep DATABASE_URL .env | cut -d/ -f4)
    
    if mysqldump -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ 数据库备份成功: $BACKUP_FILE${NC}"
    else
        echo -e "${YELLOW}⚠ 数据库备份失败（继续执行迁移）${NC}"
    fi
fi

# 检查当前数据库状态
echo ""
echo -e "${YELLOW}检查当前数据库状态...${NC}"
python3 check_db_schema.py

# 询问是否执行迁移
echo ""
read -p "是否执行数据库迁移？[Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

# 执行数据库迁移
echo ""
echo -e "${BLUE}======================================"
echo "执行数据库迁移"
echo -e "======================================${NC}"
echo ""

if alembic upgrade head; then
    echo ""
    echo -e "${GREEN}✓ 数据库迁移成功${NC}"
else
    echo ""
    echo -e "${RED}✗ 数据库迁移失败${NC}"
    exit 1
fi

# 验证修复结果
echo ""
echo -e "${BLUE}======================================"
echo "验证修复结果"
echo -e "======================================${NC}"
echo ""

python3 check_db_schema.py

# 询问是否重启服务
echo ""
read -p "是否重启应用服务？[Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if systemctl is-active --quiet display-date 2>/dev/null; then
        echo -e "${YELLOW}重启 systemd 服务...${NC}"
        sudo systemctl restart display-date
        echo -e "${GREEN}✓ 服务重启成功${NC}"
    elif pgrep -f "python.*run.py" > /dev/null; then
        echo -e "${YELLOW}重启进程...${NC}"
        pkill -f "python.*run.py"
        sleep 2
        nohup python3 run.py > logs/app.log 2>&1 &
        echo -e "${GREEN}✓ 服务重启成功${NC}"
    else
        echo -e "${YELLOW}未检测到运行中的服务${NC}"
    fi
fi

# 完成
echo ""
echo -e "${BLUE}======================================"
echo -e "${GREEN}修复完成！"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "后续步骤："
echo "1. 测试 API 接口"
echo "2. 查看日志: tail -f logs/display_date.log"
echo "3. 如有问题，从备份恢复: mysql -u用户 -p数据库 < $BACKUP_FILE"
echo ""
