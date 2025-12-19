# 🚨 立即部署指南

## ✅ 使用 SQL 管理数据库

本项目已移除数据库迁移框架，改用 SQL 脚本直接管理数据库结构。

---

## 🚀 立即执行（复制粘贴）

### 一键部署命令

```bash
ssh root@110.41.133.203 << 'ENDSSH'
cd /srv/app/display_date_python

# 1. 拉取最新代码
git pull origin master

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 使用 SQL 创建商品缓存表
mysql -u appuser -p"$(grep DATABASE_PASSWORD .env | cut -d'=' -f2)" display_date << 'EOF'
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(200) DEFAULT NULL,
    category VARCHAR(100) DEFAULT NULL,
    image VARCHAR(1024) DEFAULT NULL,
    source VARCHAR(50) DEFAULT NULL COMMENT '数据来源',
    query_count INT NOT NULL DEFAULT 0 COMMENT '查询次数',
    last_queried_at DATETIME DEFAULT NULL COMMENT '最后查询时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_products_barcode (barcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 验证表创建
SHOW TABLES LIKE 'products';
DESC products;
EOF

# 4. 重启服务
systemctl restart display_date

# 5. 查看日志
echo "等待3秒..."
sleep 3
tail -30 logs/display_date.log

# 6. 测试接口
echo "===== 测试条形码接口 ====="
curl -s "http://localhost:8000/barcode/query?code=6902363560351" \
  -H "X-OpenId: test" | python3 -m json.tool

ENDSSH
```

---

## 📋 分步执行（如果上面失败）

### 步骤1：连接服务器

```bash
ssh root@110.41.133.203
```

### 步骤2：进入项目目录

```bash
cd /srv/app/display_date_python
```

### 步骤3：拉取代码

```bash
git pull origin master
```

### 步骤4：创建表（重要！）

```bash
# 查看数据库密码
grep DATABASE_PASSWORD .env

# 进入MySQL（输入上面看到的密码）
mysql -u appuser -p display_date

# 在MySQL中执行（复制整段）
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(200) DEFAULT NULL,
    category VARCHAR(100) DEFAULT NULL,
    image VARCHAR(1024) DEFAULT NULL,
    source VARCHAR(50) DEFAULT NULL COMMENT '数据来源',
    query_count INT NOT NULL DEFAULT 0 COMMENT '查询次数',
    last_queried_at DATETIME DEFAULT NULL COMMENT '最后查询时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_products_barcode (barcode)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 验证
SHOW TABLES LIKE 'products';
DESC products;
exit
```

### 步骤5：重启服务

```bash
systemctl restart display_date
```

### 步骤6：验证

```bash
# 查看日志
tail -30 logs/display_date.log

# 测试接口
curl "http://localhost:8000/barcode/query?code=6902363560351" \
  -H "X-OpenId: test"
```

---

## ✅ 成功标志

### 1. 表已创建

```bash
mysql -u appuser -p display_date -e "DESC products;"
```

应该显示11个字段：
```
+------------------+--------------+
| Field            | Type         |
+------------------+--------------+
| id               | int          |
| barcode          | varchar(50)  |
| name             | varchar(500) |
| brand            | varchar(200) |
| category         | varchar(100) |
| image            | varchar(1024)|
| source           | varchar(50)  |
| query_count      | int          |
| last_queried_at  | datetime     |
| created_at       | datetime     |
| updated_at       | datetime     |
+------------------+--------------+
```

### 2. 服务正常运行

```bash
systemctl status display_date
```

应该显示：`active (running)`

### 3. 接口返回正常

```bash
curl "https://dhlhy.cn/barcode/query?code=6902363560351" \
  -H "X-OpenId: ofgZF1_qrt740vKblnPF4coV0so0"
```

应该返回：
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "found": true,
    "name": "得宝(Tempo)纸巾",
    "barcode": "6902363560351"
  }
}
```

---

## 🔍 故障排查

### 问题1：表已存在

如果提示表已存在，直接跳过，继续下一步。

### 问题2：MySQL密码错误

```bash
# 查看.env文件
cat .env | grep DATABASE

# 手动输入密码连接
mysql -u appuser -p display_date
```

### 问题3：服务无法启动

```bash
# 查看错误日志
tail -100 logs/display_date.log

# 或查看systemd日志
journalctl -u display_date -n 50
```

### 问题4：接口404

说明代码没更新，重新拉取：
```bash
cd /srv/app/display_date_python
git fetch origin
git reset --hard origin/master
systemctl restart display_date
```

---

## 🎯 预期结果

执行完成后：
- ✅ products 表存在
- ✅ 服务正常运行
- ✅ barcode 接口返回 200
- ✅ 扫码功能正常

---

**现在立即执行上面的命令，10分钟搞定！** 🚀

## 💡 为什么这样做？

1. **直接使用SQL**：清晰明了，完全可控
2. **IF NOT EXISTS**：如果表已存在不会报错
3. **无依赖**：不依赖任何迁移框架

这是最稳妥的方案！
