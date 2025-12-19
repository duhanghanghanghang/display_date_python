# 数据库手动管理指南

本项目不使用数据库迁移框架，所有数据库结构变更通过 SQL 脚本手动执行。

## 📋 当前表结构

### 1. users 表
```sql
CREATE TABLE users (
    openid VARCHAR(255) PRIMARY KEY,
    nickname VARCHAR(255),
    phone_number VARCHAR(32),
    avatar_url VARCHAR(1024),
    reminder_days INT NOT NULL DEFAULT 3,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 2. teams 表
```sql
CREATE TABLE teams (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_openid VARCHAR(255) NOT NULL,
    member_openids JSON NOT NULL,
    invite_code VARCHAR(64) NOT NULL,
    quota INT NOT NULL DEFAULT 5,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_teams_owner_openid (owner_openid),
    INDEX ix_teams_invite_code (invite_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3. items 表
```sql
CREATE TABLE items (
    id VARCHAR(36) PRIMARY KEY,
    owner_openid VARCHAR(255) NOT NULL,
    team_id VARCHAR(36),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    expire_date VARCHAR(255),
    note VARCHAR(1024),
    barcode VARCHAR(255),
    product_image VARCHAR(1024),
    quantity INT NOT NULL DEFAULT 1,
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at DATETIME,
    deleted_by VARCHAR(255),
    notified_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_items_owner_openid (owner_openid),
    INDEX ix_items_team_id (team_id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 4. products 表（商品缓存）
```sql
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(200),
    category VARCHAR(100),
    image VARCHAR(1024),
    source VARCHAR(50) COMMENT '数据来源',
    query_count INT NOT NULL DEFAULT 0 COMMENT '查询次数',
    last_queried_at DATETIME COMMENT '最后查询时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_products_barcode (barcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 🔧 常用操作

### 连接数据库
```bash
# 方法1：从 .env 读取配置
mysql -u appuser -p"$(grep DATABASE_PASSWORD .env | cut -d'=' -f2)" display_date

# 方法2：直接输入密码
mysql -u appuser -p display_date
```

### 查看表结构
```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESC users;
DESC teams;
DESC items;
DESC products;

-- 查看建表语句
SHOW CREATE TABLE products;
```

### 添加字段
```sql
-- 示例：给 users 表添加 email 字段
ALTER TABLE users ADD COLUMN email VARCHAR(255) AFTER phone_number;

-- 添加索引
ALTER TABLE users ADD INDEX ix_users_email (email);
```

### 修改字段
```sql
-- 修改字段类型
ALTER TABLE users MODIFY COLUMN nickname VARCHAR(500);

-- 重命名字段
ALTER TABLE users CHANGE COLUMN nickname user_nickname VARCHAR(255);
```

### 删除字段
```sql
-- 删除字段
ALTER TABLE users DROP COLUMN email;

-- 删除索引
ALTER TABLE users DROP INDEX ix_users_email;
```

### 备份数据库
```bash
# 备份整个数据库
mysqldump -u appuser -p display_date > backup_$(date +%Y%m%d_%H%M%S).sql

# 只备份表结构
mysqldump -u appuser -p --no-data display_date > schema_backup.sql

# 只备份数据
mysqldump -u appuser -p --no-create-info display_date > data_backup.sql
```

### 恢复数据库
```bash
# 从备份恢复
mysql -u appuser -p display_date < backup_20251219_120000.sql
```

## 🚨 注意事项

1. **修改前先备份**：任何结构变更前都要先备份数据库
2. **测试 SQL**：在本地测试 SQL 脚本后再在服务器执行
3. **同步代码**：修改数据库后要同步更新 `app/models.py`
4. **重启服务**：数据库变更后记得重启应用服务

## 📝 变更记录模板

```markdown
### 2025-12-19 创建 products 表
**目的**: 缓存条形码查询结果

**执行的SQL**:
CREATE TABLE products (...);

**影响**: 新增商品缓存功能

**代码变更**: app/models.py, app/routers/barcode.py
```

## 🔍 检查数据库状态

```bash
# 使用项目自带的检查工具
python3 check_db_schema.py
```

这个脚本会对比代码中的 models 和数据库实际表结构，发现差异时给出修复 SQL。
