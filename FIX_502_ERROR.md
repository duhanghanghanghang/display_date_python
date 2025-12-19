# 🚨 修复 502 Bad Gateway 错误

## 问题诊断

502 错误表示 nginx 正常运行，但无法连接到后端 Python 应用。

## 🔍 立即检查（在服务器上执行）

### 1. 检查 Python 后端服务状态

```bash
# 检查 systemd 服务状态
systemctl status display-date

# 查看服务日志（最近50行）
journalctl -u display-date -n 50 --no-pager

# 查看实时日志
journalctl -u display-date -f
```

### 2. 检查应用日志

```bash
cd /srv/app/display_date_python

# 查看最新日志
tail -f logs/display_date.log

# 查看错误日志
grep ERROR logs/display_date.log | tail -20
```

### 3. 检查端口占用

```bash
# 检查 8000 端口是否被占用
netstat -tlnp | grep 8000
# 或
ss -tlnp | grep 8000

# 检查进程
ps aux | grep python
ps aux | grep run.py
```

## 🛠️ 常见原因和解决方案

### 原因1: 应用启动失败（依赖问题）

**症状**: 服务重启后立即退出

**解决**:
```bash
cd /srv/app/display_date_python
source venv/bin/activate

# 检查依赖
pip list

# 重新安装依赖
pip install -r requirements.txt

# 手动启动测试
python3 run.py
```

### 原因2: 数据库连接失败

**症状**: 日志显示数据库连接错误

**解决**:
```bash
# 检查 MySQL 服务
systemctl status mysql

# 测试数据库连接
mysql -u appuser -p display_date

# 检查 .env 配置
cat .env | grep DATABASE
```

### 原因3: 端口冲突

**症状**: 端口已被占用

**解决**:
```bash
# 查找占用 8000 端口的进程
lsof -i:8000

# 如果是旧进程，杀掉它
kill -9 <PID>

# 重启服务
systemctl restart display-date
```

### 原因4: 虚拟环境问题

**症状**: import 错误，找不到模块

**解决**:
```bash
cd /srv/app/display_date_python

# 删除旧虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
systemctl restart display-date
```

### 原因5: systemd 服务配置问题

**检查服务配置**:
```bash
# 查看服务配置
cat /etc/systemd/system/display-date.service

# 正确的配置应该类似：
# [Service]
# WorkingDirectory=/srv/app/display_date_python
# ExecStart=/srv/app/display_date_python/venv/bin/python run.py
# Environment="PATH=/srv/app/display_date_python/venv/bin"
```

**重新加载配置**:
```bash
systemctl daemon-reload
systemctl restart display-date
```

## 🚀 快速修复脚本

创建并运行此脚本：

```bash
cat > /tmp/fix_502.sh << 'EOF'
#!/bin/bash
echo "=== 开始修复 502 错误 ==="

cd /srv/app/display_date_python

# 1. 停止服务
echo "1. 停止服务..."
systemctl stop display-date
pkill -f "python.*run.py"
sleep 2

# 2. 检查端口
echo "2. 检查端口..."
if netstat -tlnp | grep 8000; then
    echo "端口 8000 仍被占用，尝试清理..."
    fuser -k 8000/tcp
    sleep 2
fi

# 3. 激活虚拟环境并检查依赖
echo "3. 检查依赖..."
source venv/bin/activate
pip install -r requirements.txt -q

# 4. 测试启动
echo "4. 测试启动..."
timeout 5 python3 run.py &
TEST_PID=$!
sleep 3

if ps -p $TEST_PID > /dev/null; then
    echo "✅ 应用可以启动"
    kill $TEST_PID
else
    echo "❌ 应用启动失败，查看错误："
    python3 run.py
    exit 1
fi

# 5. 通过 systemd 启动
echo "5. 启动服务..."
systemctl start display-date
sleep 3

# 6. 检查状态
echo "6. 检查状态..."
if systemctl is-active --quiet display-date; then
    echo "✅ 服务运行正常"
    systemctl status display-date --no-pager
else
    echo "❌ 服务启动失败"
    journalctl -u display-date -n 20 --no-pager
    exit 1
fi

# 7. 测试连接
echo "7. 测试连接..."
sleep 2
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ API 服务正常"
else
    echo "❌ API 服务无响应"
    exit 1
fi

echo "=== 修复完成 ==="
EOF

chmod +x /tmp/fix_502.sh
bash /tmp/fix_502.sh
```

## 🔧 nginx 配置检查

虽然 nginx 运行正常，但也要确认配置：

```bash
# 检查 nginx 配置
cat /etc/nginx/sites-available/display_date

# 确保有类似配置：
# location /api/ {
#     proxy_pass http://127.0.0.1:8000/;
#     proxy_http_version 1.1;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection 'upgrade';
#     proxy_set_header Host $host;
#     proxy_cache_bypass $http_upgrade;
# }

# 测试 nginx 配置
nginx -t

# 重新加载 nginx
systemctl reload nginx
```

## 📋 完整诊断命令（一键执行）

```bash
echo "=== 502 错误诊断 ==="
echo ""
echo "1. Nginx 状态:"
systemctl status nginx --no-pager | grep Active
echo ""
echo "2. Python 服务状态:"
systemctl status display-date --no-pager | grep Active
echo ""
echo "3. 端口占用:"
netstat -tlnp | grep 8000
echo ""
echo "4. Python 进程:"
ps aux | grep python | grep -v grep
echo ""
echo "5. 最近的错误日志:"
journalctl -u display-date -n 10 --no-pager | grep -i error
echo ""
echo "6. 应用日志错误:"
tail -20 /srv/app/display_date_python/logs/display_date.log | grep ERROR
echo ""
```

## 💡 最可能的原因

根据你的情况（自动部署脚本刚执行完），最可能的原因是：

1. **依赖更新后缺少某个包** - 重新安装 requirements.txt
2. **虚拟环境路径问题** - systemd 服务配置的路径不对
3. **应用启动崩溃** - 查看 journalctl 日志

## 🎯 推荐操作顺序

1. 先执行完整诊断命令，找出问题
2. 查看 `journalctl -u display-date -n 50` 的错误信息
3. 根据错误信息选择对应的解决方案
4. 如果不确定，直接运行快速修复脚本

---

**提示**: 如果修复后问题依然存在，请提供 `journalctl` 和应用日志的错误信息，我会进一步分析。
