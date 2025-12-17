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
│   └── routers/             # API 路由
│       ├── auth.py          # 认证路由
│       ├── items.py         # 物品管理路由
│       ├── teams.py         # 团队管理路由
│       └── notify.py        # 通知路由
├── docker-compose.yml       # Docker Compose 配置
├── env.example              # 环境变量示例
├── requirements.txt         # Python 依赖
├── run.py                   # 应用启动脚本
└── README.md               # 项目文档
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

### 日志

应用日志会输出到控制台。生产环境建议配置日志文件输出。

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

## 许可证

本项目仅供学习和参考使用。
