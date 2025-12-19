"""add missing timestamp fields to all tables

Revision ID: 75a0c117de62
Revises: 
Create Date: 2025-12-19 12:23:13.493296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '75a0c117de62'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加缺失的字段到数据库表"""
    
    # 获取数据库连接
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 检查并添加 teams 表的时间戳字段
    teams_columns = [col['name'] for col in inspector.get_columns('teams')]
    if 'created_at' not in teams_columns:
        op.add_column('teams', sa.Column('created_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 teams.created_at 字段")
    
    if 'updated_at' not in teams_columns:
        op.add_column('teams', sa.Column('updated_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 teams.updated_at 字段")
    
    # 检查并添加 items 表的字段
    items_columns = [col['name'] for col in inspector.get_columns('items')]
    
    if 'quantity' not in items_columns:
        op.add_column('items', sa.Column('quantity', sa.Integer(), 
                                        server_default='1', 
                                        nullable=False))
        print("✅ 添加 items.quantity 字段")
    
    if 'created_at' not in items_columns:
        op.add_column('items', sa.Column('created_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 items.created_at 字段")
    
    if 'updated_at' not in items_columns:
        op.add_column('items', sa.Column('updated_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 items.updated_at 字段")
    
    if 'notified_at' not in items_columns:
        op.add_column('items', sa.Column('notified_at', sa.DateTime(timezone=True), 
                                        nullable=True))
        print("✅ 添加 items.notified_at 字段")
    
    # 检查并添加 users 表的时间戳字段
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'created_at' not in users_columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 users.created_at 字段")
    
    if 'updated_at' not in users_columns:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), 
                                         server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), 
                                         nullable=True))
        print("✅ 添加 users.updated_at 字段")
    
    print("✅ 数据库迁移完成")


def downgrade() -> None:
    """回滚迁移（不建议使用）"""
    # 注意：这个回滚操作会删除字段，可能导致数据丢失
    # 只在测试环境使用
    pass
