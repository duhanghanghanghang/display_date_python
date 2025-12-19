# Display Date API

基于 FastAPI + SQLAlchemy + MySQL 的物品与团队管理系统，支持微信小程序登录、JWT 鉴权、团队协作和消息通知功能。

## 技术栈

- **Web框架**: FastAPI 0.115.2
- **数据库**: MySQL 8.0 (通过 Docker Compose)
- **ORM**: SQLAlchemy 2.0.35
- **认证**: 基于 openid 的简单认证
- **异步服务器**: Uvicorn
- **消息通知**: 微信订阅消息

## 功能特性

- 🔐 微信小程序登录认证（JWT）
- 📦 物品管理（创建、查询、更新、软删除）
- 👥 团队管理（创建、加入、退出、成员管理）
- 🔗 团队邀请码机制
- 📢 微信订阅消息通知
- 🌐 CORS 跨域支持
- 📝 完整的日志系统（按天分割、自动清理、大小控制）
- 🚀 GitHub Webhook 自动部署
- 📊 统一API响应格式（标准化错误码和消息）
- 🗃️ 数据库迁移管理（Alembic）

## 快速开始

### 前置要求

- Python 3.8+
- Docker 和 Docker Compose
- MySQL 8.0 (通过 Docker)

### 安装步骤

1. **克隆项目并进入目录**
   ```bash
   cd /Users/d/Desktop/2/display_date_python
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # 或
   .venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   
   复制环境变量示例文件：
   ```bash
   cp env.example .env
   ```
   
   编辑 `.env` 文件，根据需要修改配置：
   ```env
   # 数据库配置
   DATABASE_URL=mysql+pymysql://appuser:apppassword@localhost:3306/display_date
   
   # 团队邀请码配置
   INVITE_CODE_LENGTH=8
   
   # 微信小程序配置（必填）
   WECHAT_APPID=wx5ad3bf879ec671a6
   WECHAT_SECRET=265a81a1fa7cae283ec3124d9ac05940
   WECHAT_TEMPLATE_ID=MrQmebYU1N-8tGI-9Ux1XxibqBsYuN-ncDMFkHFcdlI
   
   # GitHub Webhook 密钥（可选，用于自动部署）
   GITHUB_WEBHOOK_SECRET=your-webhook-secret-here
   
   # 服务器配置（可选）
   HOST=0.0.0.0
   PORT=8000
   RELOAD=true
   ```

5. **启动 MySQL 数据库**
   ```bash
   docker compose up -d mysql
   ```
   
   等待数据库启动完成（约10-30秒），可以检查容器状态：
   ```bash
   docker ps | grep display_date_mysql
   ```

6. **启动应用**
   
   方式一：使用 run.py（推荐）
   ```bash
   python3 run.py
   ```
   
   方式二：直接使用 uvicorn
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **验证启动**
   
   访问 http://localhost:8000 应该看到 "番茄我爱你"
   
   访问 http://localhost:8000/docs 查看 Swagger API 文档
   
   访问 http://localhost:8000/redoc 查看 ReDoc API 文档

## API 端点

### 认证相关

- `POST /login` - 微信小程序登录，获取 openid
  - 请求体: `{"code": "微信登录code"}`
  - 响应: `{"openid": "用户唯一标识"}`
  - 说明: 客户端需保存 openid，并在后续请求的 header 中携带

### 物品管理

- `GET /items` - 获取物品列表
  - 查询参数: `team_id` (可选), `include_deleted` (可选)
  - 需要认证: `Authorization: Bearer <token>`

- `POST /items` - 创建物品
  - 请求体: `{"name": "...", "expire_date": "YYYY-MM-DD", "team_id": ...}`
  - 需要认证

- `GET /items/{item_id}` - 获取单个物品详情
  - 需要认证

- `PATCH /items/{item_id}` - 更新物品
  - 请求体: `{"name": "...", "expire_date": "...", "is_deleted": ...}`
  - 需要认证

### 团队管理

- `GET /teams` - 获取用户所属团队列表
  - 需要认证

- `POST /teams` - 创建团队
  - 请求体: `{"name": "团队名称"}`
  - 需要认证

- `GET /teams/{team_id}` - 获取团队详情
  - 需要认证

- `PATCH /teams/{team_id}/rename` - 重命名团队
  - 请求体: `{"name": "新名称"}`
  - 需要认证（仅团队创建者）

- `POST /teams/join` - 通过邀请码加入团队
  - 请求体: `{"invite_code": "..."}`
  - 需要认证

- `POST /teams/{team_id}/reset-invite-code` - 重置团队邀请码
  - 需要认证（仅团队创建者）

- `POST /teams/{team_id}/remove-member` - 移除团队成员
  - 请求体: `{"openid": "..."}`
  - 需要认证（仅团队创建者）

- `POST /teams/{team_id}/exit` - 退出团队
  - 需要认证

### 通知相关

- `POST /notify/subscribe` - 订阅消息通知
  - 需要认证

### Webhook（自动部署）

- `POST /webhook/github` - GitHub Webhook 端点
  - 接收 GitHub 推送通知并自动部署
  - 需要配置 webhook 密钥
  - 详见：[WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)

- `GET /webhook/test` - 测试 Webhook 端点
  - 返回: `{"message": "Webhook endpoint is working"}`

所有需要认证的接口都需要在请求头中包含 openid，支持两种方式：
```
X-OpenId: <your_openid>
或
openid: <your_openid>
```

示例：
```bash
curl -H "X-OpenId: your_openid_here" http://localhost:8000/items
```

## 项目结构

```
display_date_python/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接和会话
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── schemas.py           # Pydantic 数据模式
│   ├── auth.py              # JWT 认证逻辑
│   ├── env_loader.py        # 环境变量加载
│   ├── notifier.py          # 消息通知服务
│   ├── wechat.py            # 微信 API 集成
│   ├── logger.py            # 日志管理系统
│   ├── middleware.py        # 中间件（日志记录、错误处理）
│   └── routers/             # API 路由
│       ├── auth.py          # 认证路由
│       ├── items.py         # 物品管理路由
│       ├── teams.py         # 团队管理路由
│       ├── notify.py        # 通知路由
│       └── webhook.py       # Webhook 路由（自动部署）
├── logs/                    # 日志文件夹（自动创建）
│   └── display_date.log    # 应用日志
├── docker-compose.yml       # Docker Compose 配置
├── env.example              # 环境变量示例
├── requirements.txt         # Python 依赖
├── run.py                   # 应用启动脚本
├── auto_deploy.sh           # 自动部署脚本
├── clean_logs.py            # 日志清理工具
├── WEBHOOK_SETUP.md         # Webhook 配置指南
└── README.md               # 项目文档
```

## 日志系统

### 功能特性

- ✅ **单独的日志文件夹**：所有日志存储在 `logs/` 目录
- ✅ **按天分割**：每天午夜自动创建新的日志文件
- ✅ **自动保留一周**：只保留最近 7 天的日志
- ✅ **大小控制**：日志总大小超过 2GB 时自动清理最旧的日志
- ✅ **请求日志**：记录所有 API 请求、响应状态码和耗时
- ✅ **错误日志**：记录异常和错误堆栈信息
- ✅ **自动清理**：每次应用启动时自动执行日志清理

### 手动清理日志

如果需要手动清理日志：

```bash
python3 clean_logs.py
```

### 定时清理（Cron）

可以设置 cron 任务定期清理日志：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点清理）
0 2 * * * cd /path/to/display_date_python && /path/to/python3 clean_logs.py
```

### 查看日志

```bash
# 实时查看日志
tail -f logs/display_date.log

# 查看最近 100 行
tail -n 100 logs/display_date.log

# 搜索错误日志
grep ERROR logs/display_date.log
```

## 自动部署

### 配置步骤

1. **配置 webhook 密钥**：
   ```bash
   # 生成随机密钥
   openssl rand -hex 32
   # 将密钥添加到 .env 文件
   echo "GITHUB_WEBHOOK_SECRET=your-secret-key" >> .env
   ```

2. **在 GitHub 仓库中配置 Webhook**：
   - 进入仓库 Settings > Webhooks > Add webhook
   - Payload URL: `https://your-domain.com/webhook/github`
   - Content type: `application/json`
   - Secret: 填入上面生成的密钥
   - 选择 "Just the push event"
   - 勾选 "Active"

3. **重启应用**：
   ```bash
   sudo systemctl restart display-date
   ```

详细配置步骤请查看：[WEBHOOK_SETUP.md](WEBHOOK_SETUP.md)

### 工作流程

```
推送代码到 GitHub → GitHub 发送 Webhook → 服务器接收并验证
→ 后台执行部署脚本 → 拉取最新代码 → 更新依赖 → 清理日志 → 重启服务
```

### 手动部署

如果需要手动部署：

```bash
bash auto_deploy.sh
```

## 数据库

数据库通过 Docker Compose 管理，默认配置：
- 端口: 3306
- 数据库名: `display_date`
- 用户名: `appuser`
- 密码: `apppassword`
- 字符集: utf8mb4
- 时区: Asia/Shanghai

数据会持久化保存在 Docker volume `mysql_data` 中。

## 开发说明

### 环境变量

应用启动时会自动加载 `.env` 文件中的环境变量。也可以通过系统环境变量设置，优先级高于 `.env` 文件。

### 数据库迁移

当前使用 SQLAlchemy 的 `Base.metadata.create_all()` 自动创建表结构。生产环境建议使用 Alembic 进行数据库迁移管理。

### 日志管理

- 日志文件位于 `logs/` 目录
- 应用启动时自动清理过期日志
- 可以手动运行 `python3 clean_logs.py` 清理日志
- 建议配置 cron 定期清理

## 常见问题

1. **数据库连接失败**
   - 确保 MySQL 容器已启动: `docker ps | grep mysql`
   - 检查 `.env` 中的 `DATABASE_URL` 配置是否正确
   - 等待数据库完全启动（首次启动可能需要30秒）

2. **端口被占用**
   - 修改 `.env` 中的 `PORT` 配置
   - 或使用 `--port` 参数指定其他端口

3. **依赖安装失败**
   - 确保使用 Python 3.8+
   - 尝试升级 pip: `pip install --upgrade pip`

## 相关文档

### 📚 完整文档列表

#### 入门文档
- 📖 [README.md](README.md) - 项目总览（你正在阅读）
- 🚀 [QUICK_START.md](QUICK_START.md) - 快速开始指南
- 📋 [UPDATE_SUMMARY.md](UPDATE_SUMMARY.md) - 最新更新说明

#### API开发
- 📊 [API_RESPONSE_FORMAT.md](API_RESPONSE_FORMAT.md) - **API响应格式规范**
- 📱 [小程序端集成示例.md](小程序端集成示例.md) - 小程序端代码示例

#### 数据库
- 🗃️ [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) - 数据库迁移指南（Alembic）

#### 部署运维
- 🔧 [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) - Webhook首次配置
- 🛠️ [WEBHOOK_FIX.md](WEBHOOK_FIX.md) - **Webhook故障修复**
- 🐛 [DEPLOYMENT_ERROR_FIX.md](DEPLOYMENT_ERROR_FIX.md) - 部署错误修复

#### 在线文档
- 📄 API文档: http://your-server:8000/docs
- 📄 ReDoc: http://your-server:8000/redoc

---

## 许可证

本项目仅供学习和参考使用。
