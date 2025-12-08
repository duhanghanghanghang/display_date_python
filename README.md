# FastAPI 物品与团队管理示例

基于 FastAPI + SQLAlchemy + MySQL（docker），实现了登录、物品、团队接口，并使用 JWT 进行鉴权。

## 快速开始

1. 安装依赖
   ```bash
   cd /Users/d/Desktop/display_date_python
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 启动数据库（MySQL）
   ```bash
   docker compose up -d mysql
   ```
3. 配置环境变量  
   复制 `env.example` 为 `.env`（或直接在环境中导出），根据需要修改：
   ```
   DATABASE_URL=mysql+pymysql://appuser:apppassword@localhost:3306/display_date
   JWT_SECRET=change-me
   JWT_EXPIRES_MINUTES=1440
   INVITE_CODE_LENGTH=8
   ```
4. 运行应用
   ```bash
   uvicorn app.main:app --reload
   ```

## 主要端点
- `POST /login` 获取 token（示例使用 code 直接作为 openid）。
- `GET/POST/PATCH /items` 系列：个人或团队物品，含软删。
- `GET/POST/PATCH /teams` 系列：创建、加入、重命名、重置邀请码、移除成员、退出。

所有接口需 `Authorization: Bearer <token>`。

