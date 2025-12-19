#!/usr/bin/env python3
"""
检查数据库表结构并生成修复SQL
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.database import engine
from app.models import Team, Item, User

def check_table_columns():
    """检查表的字段"""
    inspector = inspect(engine)
    
    print("=" * 60)
    print("检查数据库表结构")
    print("=" * 60)
    print()
    
    # 检查每个表
    for table_name in ['teams', 'items', 'users']:
        print(f"表: {table_name}")
        print("-" * 60)
        
        if not inspector.has_table(table_name):
            print(f"  ❌ 表不存在")
            continue
        
        columns = inspector.get_columns(table_name)
        column_names = [col['name'] for col in columns]
        
        print(f"  现有字段: {', '.join(column_names)}")
        
        # 获取模型中期望的字段
        if table_name == 'teams':
            model = Team
        elif table_name == 'items':
            model = Item
        elif table_name == 'users':
            model = User
        
        model_columns = [col.name for col in model.__table__.columns]
        print(f"  模型字段: {', '.join(model_columns)}")
        
        # 找出缺失的字段
        missing = set(model_columns) - set(column_names)
        extra = set(column_names) - set(model_columns)
        
        if missing:
            print(f"  ⚠️  缺失字段: {', '.join(missing)}")
        if extra:
            print(f"  ⚠️  多余字段: {', '.join(extra)}")
        
        if not missing and not extra:
            print(f"  ✅ 字段完全匹配")
        
        print()
    
    print("=" * 60)
    print("建议的修复SQL")
    print("=" * 60)
    print()
    
    # 生成修复SQL
    fix_sql = []
    
    # 检查 teams 表
    teams_columns = [col['name'] for col in inspector.get_columns('teams')]
    if 'created_at' not in teams_columns:
        fix_sql.append("ALTER TABLE teams ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
    if 'updated_at' not in teams_columns:
        fix_sql.append("ALTER TABLE teams ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;")
    
    # 检查 items 表
    items_columns = [col['name'] for col in inspector.get_columns('items')]
    if 'quantity' not in items_columns:
        fix_sql.append("ALTER TABLE items ADD COLUMN quantity INT DEFAULT 1 NOT NULL;")
    if 'created_at' not in items_columns:
        fix_sql.append("ALTER TABLE items ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
    if 'updated_at' not in items_columns:
        fix_sql.append("ALTER TABLE items ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;")
    
    # 检查 users 表
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'created_at' not in users_columns:
        fix_sql.append("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
    if 'updated_at' not in users_columns:
        fix_sql.append("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;")
    
    if fix_sql:
        print("需要执行以下SQL修复数据库：")
        print()
        for sql in fix_sql:
            print(f"  {sql}")
        print()
        print("运行方法:")
        print("  方法1: alembic upgrade head")
        print("  方法2: 手动连接数据库执行上述SQL")
    else:
        print("✅ 数据库表结构完全正确，无需修复")

if __name__ == "__main__":
    try:
        check_table_columns()
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
