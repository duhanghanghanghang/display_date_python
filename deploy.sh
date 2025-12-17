#!/bin/bash

# Display Date 服务器部署脚本
# 使用方法：bash deploy.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "Display Date 部署脚本"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在正确的目录
if [ ! -f "run.py" ]; then
    echo -e "${RED}错误：请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 Python 版本
echo -e "${YELLOW}检查 Python 版本...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate

# 升级 pip
echo -e "${YELLOW}升级 pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip 已升级${NC}"

# 安装依赖
echo -e "${YELLOW}安装依赖...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo -e "${YELLOW}复制环境变量示例文件...${NC}"
        cp env.example .env
        echo -e "${YELLOW}⚠ 请编辑 .env 文件配置数据库等信息${NC}"
        echo -e "${YELLOW}  编辑命令: nano .env${NC}"
        read -p "按 Enter 继续编辑 .env 文件..."
        nano .env
    else
        echo -e "${RED}错误：找不到 env.example 文件${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

# 检查数据库连接
echo -e "${YELLOW}检查数据库连接...${NC}"
python3 -c "from app.database import engine; engine.connect()" 2>/dev/null && \
    echo -e "${GREEN}✓ 数据库连接成功${NC}" || \
    echo -e "${RED}✗ 数据库连接失败，请检查 .env 配置${NC}"

# 询问是否创建 systemd 服务
echo ""
read -p "是否创建 systemd 服务（开机自启）？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    
    echo -e "${YELLOW}创建 systemd 服务文件...${NC}"
    
    sudo tee /etc/systemd/system/display-date.service > /dev/null << EOF
[Unit]
Description=Display Date API Service
After=network.target mysql.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python3 $CURRENT_DIR/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}✓ systemd 服务文件创建完成${NC}"
    
    # 重新加载 systemd
    sudo systemctl daemon-reload
    
    # 启动服务
    sudo systemctl start display-date
    
    # 设置开机自启
    sudo systemctl enable display-date
    
    echo -e "${GREEN}✓ 服务已启动并设置为开机自启${NC}"
    
    # 显示服务状态
    echo ""
    echo -e "${YELLOW}服务状态：${NC}"
    sudo systemctl status display-date --no-pager
else
    echo -e "${YELLOW}跳过 systemd 服务创建${NC}"
    echo -e "${YELLOW}手动启动命令: python3 run.py${NC}"
fi

# 询问是否配置 Nginx
echo ""
read -p "是否配置 Nginx 反向代理？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "请输入域名（例如：example.com）: " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}错误：域名不能为空${NC}"
    else
        echo -e "${YELLOW}创建 Nginx 配置...${NC}"
        
        sudo tee /etc/nginx/sites-available/display-date > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

        # 创建软链接
        if [ ! -L /etc/nginx/sites-enabled/display-date ]; then
            sudo ln -s /etc/nginx/sites-available/display-date /etc/nginx/sites-enabled/
        fi
        
        # 测试配置
        sudo nginx -t && \
            echo -e "${GREEN}✓ Nginx 配置正确${NC}" || \
            echo -e "${RED}✗ Nginx 配置错误${NC}"
        
        # 重启 Nginx
        sudo systemctl restart nginx
        echo -e "${GREEN}✓ Nginx 已重启${NC}"
        
        # 提示配置 SSL
        echo ""
        echo -e "${YELLOW}建议配置 SSL 证书：${NC}"
        echo "  sudo certbot --nginx -d $DOMAIN"
    fi
else
    echo -e "${YELLOW}跳过 Nginx 配置${NC}"
fi

# 完成
echo ""
echo "======================================"
echo -e "${GREEN}部署完成！${NC}"
echo "======================================"
echo ""
echo "后续操作："
echo "1. 查看服务状态：sudo systemctl status display-date"
echo "2. 查看日志：sudo journalctl -u display-date -f"
echo "3. 停止服务：sudo systemctl stop display-date"
echo "4. 重启服务：sudo systemctl restart display-date"
echo ""
echo "API 地址："
echo "  本地：http://127.0.0.1:8000"
if [ ! -z "$DOMAIN" ]; then
    echo "  域名：http://$DOMAIN"
fi
echo ""
echo "API 文档："
if [ ! -z "$DOMAIN" ]; then
    echo "  http://$DOMAIN/docs"
else
    echo "  http://127.0.0.1:8000/docs"
fi
echo ""
echo -e "${GREEN}备案信息已添加到首页${NC}"
echo "备案号：渝ICP备2025076154号"
echo ""

