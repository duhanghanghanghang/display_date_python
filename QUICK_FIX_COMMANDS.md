# 快速修复命令清单

## 🚨 立即修复 Webhook

### 在本地（推送代码自动部署）

```bash
cd /Users/d/Desktop/2/display_date_python

# 添加所有更改
git add .

# 提交
git commit -m "修复webhook并添加统一API响应格式"

# 推送到服务器
git push origin master
```

推送后，服务器会自动：
1. 拉取最新代码
2. 安装依赖
3. 执行数据库迁移
4. 重启服务

等待30-60秒后，webhook应该就能正常工作了。

---

### 在服务器（如需立即修复）

```bash
# SSH连接到服务器
ssh user@your-server

# 进入项目目录
cd /srv/app/display_date_python  # 改为你的实际路径

# 激活虚拟环境
source venv/bin/activate

# 拉取最新代码
git pull origin master

# 安装新依赖（如有）
pip install -r requirements.txt

# 重启服务
sudo systemctl restart display-date

# 查看状态
sudo systemctl status display-date
```

---

## ✅ 验证修复

### 1. 测试 Webhook 端点

```bash
curl https://your-domain.com/webhook/test
```

**预期结果**：
```json
{"message": "Webhook endpoint is working"}
```

### 2. 检查 GitHub Webhook

1. 访问：`https://github.com/你的用户名/你的仓库/settings/hooks`
2. 点击你的 webhook
3. 查看 **Recent Deliveries**
4. 最新的推送应该显示：
   - ✓ 绿色勾（成功）
   - Response code: `200`
   - Response body: `{"message": "Deployment started"}` 或类似

### 3. 查看服务器日志

```bash
# 实时查看日志
tail -f /path/to/logs/display_date.log

# 查看 webhook 相关日志
grep webhook /path/to/logs/display_date.log | tail -20
```

**预期输出**：
```
2025-12-19 12:30:00 - INFO - 收到 GitHub webhook 事件: push
2025-12-19 12:30:00 - INFO - GitHub webhook 签名验证通过
2025-12-19 12:30:00 - INFO - 收到推送: user/repo | 分支: refs/heads/master
2025-12-19 12:30:00 - INFO - 已将部署任务加入后台队列
```

---

## 🔄 测试自动部署

### 方式1：空提交测试

```bash
git commit --allow-empty -m "Test webhook auto deploy"
git push
```

然后查看：
1. GitHub webhook 推送记录
2. 服务器日志
3. 代码是否更新

### 方式2：修改README测试

```bash
echo "\n测试 $(date)" >> README.md
git add README.md
git commit -m "Test auto deploy"
git push
```

---

## 🛠️ 如果仍然失败

### 检查清单

```bash
# 1. 服务是否运行
sudo systemctl status display-date

# 2. 代码是否最新
cd /path/to/project
git log -1 --oneline

# 3. webhook密钥是否配置
cat .env | grep GITHUB_WEBHOOK_SECRET

# 4. 端口是否开放
sudo netstat -tlnp | grep 8000

# 5. Nginx配置是否正确
sudo nginx -t
```

### 重新配置 Webhook 密钥

```bash
# 生成新密钥
NEW_SECRET=$(openssl rand -hex 32)

# 更新 .env
echo "GITHUB_WEBHOOK_SECRET=$NEW_SECRET" >> .env

# 显示密钥（复制到GitHub）
echo "新的webhook密钥: $NEW_SECRET"

# 重启服务
sudo systemctl restart display-date
```

然后：
1. 进入 GitHub → Settings → Webhooks → Edit
2. 更新 Secret 字段
3. 点击 "Update webhook"
4. 点击 "Redeliver" 重新发送测试

---

## 📊 数据库问题修复

如果遇到"Unknown column"错误：

```bash
cd /path/to/project
source venv/bin/activate

# 检查数据库状态
python3 check_db_schema.py

# 使用 SQL 脚本修复数据库
# mysql -u用户 -p数据库 < fix.sql

# 重启服务
sudo systemctl restart display-date
```

---

## 🔍 日志查看命令

```bash
# 实时查看所有日志
tail -f logs/display_date.log

# 只看错误
tail -f logs/display_date.log | grep ERROR

# 只看 webhook
tail -f logs/display_date.log | grep webhook

# 查看最近50行
tail -50 logs/display_date.log

# 查看特定时间段
grep "2025-12-19 12:" logs/display_date.log
```

---

## 📞 获取帮助

### 问题诊断

1. **Webhook问题**：查看 [WEBHOOK_FIX.md](WEBHOOK_FIX.md)
2. **API格式问题**：查看 [API_RESPONSE_FORMAT.md](API_RESPONSE_FORMAT.md)
3. **数据库问题**：使用 SQL 脚本手动修复

### 查看完整日志

```bash
# 导出今天的日志
grep "$(date +%Y-%m-%d)" logs/display_date.log > debug_$(date +%Y%m%d).log

# 查看大小
ls -lh debug_*.log
```

---

**按照以上步骤，webhook应该可以正常工作了！** 🎉

如有问题，查看完整文档或检查服务器日志。
