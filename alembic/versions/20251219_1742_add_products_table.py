"""添加商品库表products

Revision ID: 20251219_1742
Revises: 20251219_1223_75a0c117de62
Create Date: 2025-12-19 17:42:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20251219_1742'
down_revision: Union[str, None] = '20251219_1223_75a0c117de62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建商品库表"""
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('barcode', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('brand', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('image', sa.String(length=1024), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True, comment='数据来源: local/openfoodfacts/upcitemdb/user'),
        sa.Column('query_count', sa.Integer(), nullable=False, server_default='0', comment='查询次数'),
        sa.Column('last_queried_at', mysql.DATETIME(timezone=True), nullable=True, comment='最后查询时间'),
        sa.Column('created_at', mysql.DATETIME(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', mysql.DATETIME(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('barcode'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 创建索引
    op.create_index('ix_products_barcode', 'products', ['barcode'], unique=True)


def downgrade() -> None:
    """删除商品库表"""
    op.drop_index('ix_products_barcode', table_name='products')
    op.drop_table('products')
