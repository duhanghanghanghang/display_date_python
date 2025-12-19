# 新功能快速开始指南

## 🎉 新增功能

### 1. 完整的日志系统 📝

#### 功能特性
- ✅ 单独的 `logs/` 文件夹存储所有日志
- ✅ 每天午夜自动分割日志文件
- ✅ 自动保留最近 7 天的日志
- ✅ 日志总大小超过 2GB 时自动清理最旧的日志
- ✅ 记录所有 API 请求、响应和错误
- ✅ 每次应用启动时自动执行日志清理

#### 使用方法

**查看日志：**
```bash
# 实时查看日志
tail -f logs/display_date.log

# 查看最近 100 行
tail -n 100 logs/display_date.log

# 搜索错误
grep ERROR logs/display_date.log

# 搜索特定请求
grep "POST /items" logs/display_date.log
```

**手动清理日志：**
```bash
python3 clean_logs.py
```

**设置定时清理（可选）：**
```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点清理）
0 2 * * * cd /path/to/display_date_python && python3 clean_logs.py
```

#### 日志内容示例

```
2025-12-19 10:30:15 - display_date - INFO - 应用启动中...
2025-12-19 10:30:15 - display_date - INFO - 开始日志清理
2025-12-19 10:30:15 - display_date - INFO - 日志总大小: 0.15 GB (未超限)
2025-12-19 10:30:15 - display_date - INFO - 应用启动完成
2025-12-19 10:30:20 - display_date - INFO - 请求开始 | GET /items | 客户端: 192.168.1.100
2025-12-19 10:30:20 - display_date - INFO - 请求完成 | GET /items | 状态码: 200 | 耗时: 0.025s
2025-12-19 10:30:25 - display_date - ERROR - 请求异常 | POST /items | 耗时: 0.010s | 错误: ...
```

---

### 2. GitHub Webhook 自动部署 🚀

#### 功能特性
- ✅ GitHub 推送代码后自动拉取最新代码
- ✅ 自动安装/更新依赖
- ✅ 自动清理日志
- ✅ 自动重启服务
- ✅ 支持签名验证，确保安全
- ✅ 后台执行，不阻塞 API 服务

#### 配置步骤

**步骤 1：配置服务器**

1. 生成 webhook 密钥：
   ```bash
   openssl rand -hex 32
   ```

2. 将密钥添加到 `.env` 文件：
   ```bash
   echo "GITHUB_WEBHOOK_SECRET=your-generated-secret" >> .env
   ```

3. 重启应用：
   ```bash
   sudo systemctl restart display-date
   # 或
   docker-compose restart
   ```

**步骤 2：配置 GitHub**

1. 打开 GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**

2. 填写配置：
   - **Payload URL**: `https://your-domain.com/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: 填入上面生成的密钥
   - **Which events**: 选择 "Just the push event"
   - 勾选 **Active**

3. 点击 **Add webhook**

**步骤 3：测试**

1. 测试端点是否可访问：
   ```bash
   curl https://your-domain.com/webhook/test
   ```
   
   应该返回：
   ```json
   {"message": "Webhook endpoint is working"}
   ```

2. 推送代码测试：
   ```bash
   git add .
   git commit -m "Test webhook"
   git push origin master
   ```

3. 查看 GitHub webhook 推送记录：
   - 进入 Settings → Webhooks → 点击你的 webhook
   - 点击 **Recent Deliveries** 查看推送历史

4. 查看服务器日志：
   ```bash
   tail -f logs/display_date.log
   ```
   
   你应该能看到类似的日志：
   ```
   2025-12-19 10:30:00 - INFO - 收到 GitHub webhook 事件: push
   2025-12-19 10:30:00 - INFO - 收到推送: your-repo | 分支: refs/heads/master
   2025-12-19 10:30:00 - INFO - 已将部署任务加入后台队列
   2025-12-19 10:30:01 - INFO - 开始执行自动部署...
   2025-12-19 10:30:05 - INFO - 自动部署成功完成
   ```

#### 手动部署

如果需要手动部署（不通过 webhook）：

```bash
bash auto_deploy.sh
```

#### 工作流程

```
你推送代码 → GitHub 发送 Webhook → 服务器接收并验证
→ 后台执行部署脚本 → 拉取代码 → 更新依赖 → 清理日志 → 重启服务
```

---

## 📋 完整的服务器配置检查清单

### 必需配置

- [ ] 安装 Python 3.8+
- [ ] 安装 MySQL 8.0
- [ ] 复制 `env.example` 到 `.env` 并配置数据库连接
- [ ] 配置微信小程序 APPID 和 SECRET
- [ ] 安装依赖：`pip install -r requirements.txt`

### 日志系统配置

- [ ] 确认 `logs/` 文件夹会自动创建
- [ ] （可选）配置 cron 定时清理日志

### 自动部署配置

- [ ] 生成并配置 `GITHUB_WEBHOOK_SECRET`
- [ ] 确保服务器有公网 IP 或域名
- [ ] 配置 GitHub Webhook
- [ ] 测试 webhook 端点可访问
- [ ] 设置 `auto_deploy.sh` 为可执行：`chmod +x auto_deploy.sh`

### 生产环境配置

- [ ] 配置 systemd 服务或 Docker
- [ ] 配置 Nginx 反向代理
- [ ] 配置 SSL 证书（Let's Encrypt）
- [ ] 设置防火墙规则
- [ ] 配置日志轮转
- [ ] 设置监控和告警

---

## 🔍 故障排查

### 日志相关问题

**问题：日志文件夹不存在**
```bash
# 手动创建
mkdir logs
```

**问题：日志文件权限错误**
```bash
# 修复权限
chmod 755 logs
chmod 644 logs/*.log
```

**问题：日志文件太大**
```bash
# 手动清理
python3 clean_logs.py
```

### Webhook 相关问题

**问题：Webhook 未触发**
- 检查 GitHub webhook 推送记录是否有错误
- 确认服务器可以从外网访问
- 查看服务器日志：`tail -f logs/display_date.log`

**问题：签名验证失败**
- 确保 `.env` 中的密钥与 GitHub 配置一致
- 重启服务使配置生效

**问题：部署失败**
```bash
# 查看详细日志
bash -x auto_deploy.sh

# 检查权限
chmod +x auto_deploy.sh

# 手动执行测试
bash auto_deploy.sh
```

---

## 📚 更多文档

- **Webhook 详细配置**：查看 [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)
- **API 文档**：访问 `http://your-server:8000/docs`
- **项目说明**：查看 [README.md](README.md)

---

## 🎯 下一步

1. **测试日志系统**：
   ```bash
   # 启动应用
   python3 run.py
   
   # 发送一些测试请求
   curl http://localhost:8000/
   
   # 查看日志
   tail -f logs/display_date.log
   ```

2. **配置自动部署**：
   - 按照上面的步骤配置 webhook
   - 推送一次代码测试

3. **监控日志大小**：
   ```bash
   # 查看日志文件夹大小
   du -sh logs/
   
   # 查看所有日志文件
   ls -lh logs/
   ```

---

## ✨ 享受自动化部署！

配置完成后，你只需要：
```bash
git add .
git commit -m "Update code"
git push
```

服务器就会自动更新代码并重新部署！🚀
