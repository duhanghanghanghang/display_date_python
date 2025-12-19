# 数据库迁移指南 (Alembic)

## 🎯 概述

本项目使用 **Alembic** 进行数据库迁移管理。当你在代码中修改数据模型（`app/models.py`）后，Alembic 可以自动生成迁移脚本并更新数据库表结构。

## ✨ 功能特性

- ✅ **自动检测模型变化**：添加/删除/修改字段时自动生成迁移脚本
- ✅ **版本控制**：所有数据库变更都有版本记录
- ✅ **可回滚**：支持升级和降级操作
- ✅ **自动部署集成**：推送代码后自动执行数据库迁移
- ✅ **安全检查**：迁移前会检查字段是否已存在

---

## 📦 快速开始

### 1. 安装依赖

已包含在 `requirements.txt` 中，安装项目依赖即可：

```bash
pip install -r requirements.txt
```

### 2. 初始配置

Alembic 已经配置好，配置文件：
- `alembic.ini` - Alembic 配置
- `alembic/env.py` - 环境配置（已配置为从 `.env` 读取数据库连接）

---

## 🚀 常用命令

### 查看当前数据库版本

```bash
alembic current
```

### 查看迁移历史

```bash
alembic history
```

### 升级到最新版本（执行所有未执行的迁移）

```bash
alembic upgrade head
```

### 生成新的迁移脚本（自动检测模型变化）

```bash
# 自动检测模型变化
alembic revision --autogenerate -m "描述你的变更"

# 例如：
alembic revision --autogenerate -m "add user avatar field"
```

### 手动创建迁移脚本

```bash
alembic revision -m "描述你的变更"
```

### 回滚到上一个版本

```bash
alembic downgrade -1
```

### 回滚到特定版本

```bash
alembic downgrade <revision_id>
```

---

## 📝 工作流程

### 场景1：修改现有模型（添加字段）

**步骤 1**：修改 `app/models.py`

```python
class Item(TimestampMixin, Base):
    __tablename__ = "items"
    
    # ... 现有字段 ...
    
    # 添加新字段
    status = Column(String(50), nullable=True, default="active")
```

**步骤 2**：生成迁移脚本

```bash
alembic revision --autogenerate -m "add status field to items"
```

**步骤 3**：检查生成的迁移脚本

```bash
# 查看最新的迁移文件
ls -lt alembic/versions/

# 编辑并检查迁移脚本
nano alembic/versions/最新文件.py
```

**步骤 4**：执行迁移

```bash
alembic upgrade head
```

**步骤 5**：验证

```bash
# 运行检查脚本
python3 check_db_schema.py
```

---

### 场景2：创建新表

**步骤 1**：在 `app/models.py` 中创建新模型

```python
class Product(TimestampMixin, Base):
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
```

**步骤 2**：在 `alembic/env.py` 中导入新模型

```python
from app.models import Team, Item, User, Product  # 添加 Product
```

**步骤 3**：生成并执行迁移

```bash
alembic revision --autogenerate -m "create products table"
alembic upgrade head
```

---

### 场景3：删除字段

**步骤 1**：从 `app/models.py` 中删除字段

**步骤 2**：生成迁移脚本

```bash
alembic revision --autogenerate -m "remove old field"
```

**步骤 3**：**仔细检查**生成的迁移脚本

⚠️ **警告**：删除字段会丢失数据！确保：
- 数据已备份
- 应用代码不再使用该字段
- 在生产环境谨慎操作

**步骤 4**：执行迁移

```bash
alembic upgrade head
```

---

## 🔧 服务器部署

### 方式1：自动部署（推荐）

配置 GitHub Webhook 后，推送代码会自动执行数据库迁移：

```bash
git add .
git commit -m "Add new field to user model"
git push

# 服务器会自动：
# 1. 拉取代码
# 2. 安装依赖
# 3. 执行 alembic upgrade head ✅
# 4. 重启服务
```

### 方式2：手动部署

SSH 连接到服务器后：

```bash
cd /path/to/display_date_python
source venv/bin/activate

# 拉取最新代码
git pull

# 执行数据库迁移
alembic upgrade head

# 重启服务
sudo systemctl restart display-date
```

---

## 🛠️ 实用工具

### 检查数据库表结构

```bash
python3 check_db_schema.py
```

这个脚本会：
- 显示每个表的现有字段
- 显示模型中定义的字段
- 指出缺失或多余的字段
- 建议修复SQL

### 查看待执行的迁移

```bash
alembic show head
alembic current
```

如果 `current` 版本低于 `head` 版本，说明有未执行的迁移。

---

## ⚠️ 注意事项

### 1. 生产环境操作

**迁移前务必：**
- ✅ 备份数据库
- ✅ 在测试环境验证
- ✅ 选择低流量时段
- ✅ 准备回滚方案

**执行迁移：**
```bash
# 1. 备份数据库
mysqldump -u appuser -p display_date > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 执行迁移
alembic upgrade head

# 3. 验证
python3 check_db_schema.py
```

### 2. 冲突处理

如果多个开发者同时创建迁移脚本，可能产生冲突：

```bash
# 查看冲突的迁移
alembic branches

# 合并分支（需要手动编辑迁移文件）
alembic merge -m "merge migrations" <rev1> <rev2>
```

### 3. 迁移失败恢复

如果迁移失败：

```bash
# 方式1：回滚到上一个版本
alembic downgrade -1

# 方式2：回滚到特定版本
alembic current  # 查看当前版本
alembic downgrade <revision_id>

# 方式3：从备份恢复
mysql -u appuser -p display_date < backup_20251219.sql
```

---

## 📚 常见问题

### Q1: 迁移脚本没有检测到我的模型变化？

**A**: 确保：
1. 模型类已在 `alembic/env.py` 中导入
2. 模型继承自 `Base`
3. 运行命令前已保存文件

### Q2: 如何查看某个迁移的详细内容？

**A**: 
```bash
cat alembic/versions/<revision_id>_*.py
```

### Q3: 可以手动编辑迁移脚本吗？

**A**: 可以！生成后可以编辑 `upgrade()` 和 `downgrade()` 函数。常见场景：
- 添加数据迁移逻辑
- 修改字段默认值
- 添加索引
- 批量更新数据

### Q4: 如何跳过某个有问题的迁移？

**A**: 
```bash
# 标记为已执行（不实际运行）
alembic stamp <revision_id>

# 或者删除有问题的迁移文件，重新生成
rm alembic/versions/有问题的文件.py
alembic revision --autogenerate -m "recreate migration"
```

### Q5: 本地开发和服务器数据库结构不一致怎么办？

**A**: 
```bash
# 在两个环境分别运行
python3 check_db_schema.py

# 如果服务器缺少字段，在服务器上运行
alembic upgrade head
```

---

## 🎯 最佳实践

### 1. 频繁提交小迁移

✅ **好的做法**：
```bash
# 迁移1：添加字段
alembic revision --autogenerate -m "add avatar field"

# 迁移2：添加索引
alembic revision --autogenerate -m "add index on email"
```

❌ **不好的做法**：
```bash
# 一个大迁移包含很多变更
alembic revision --autogenerate -m "update all models"
```

### 2. 清晰的迁移描述

✅ **好的描述**：
- `add user avatar field`
- `create products table`
- `remove deprecated status column`

❌ **不好的描述**：
- `update`
- `fix`
- `changes`

### 3. 测试迁移

每个迁移都应该测试：
```bash
# 测试升级
alembic upgrade head

# 测试回滚（在测试环境）
alembic downgrade -1

# 再次升级
alembic upgrade head
```

### 4. 不要直接修改已部署的迁移

如果迁移已经在生产环境执行，不要修改它。应该：
- 创建新的迁移来修正
- 保持迁移历史的完整性

---

## 📖 更多资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [项目 README](README.md)
- [自动部署指南](WEBHOOK_SETUP.md)

---

## 🎉 总结

使用 Alembic 后，数据库结构变更流程：

```
修改 models.py → alembic revision --autogenerate → alembic upgrade head → 完成！
```

或者更简单的自动部署流程：

```
修改 models.py → git push → 服务器自动迁移 → 完成！
```

**再也不用手写 SQL 来修改数据库结构了！** 🚀
