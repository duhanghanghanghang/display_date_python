from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from .database import Base


class TimestampMixin:
    """通用创建/更新时间字段，使用东八区会话时区。"""

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    owner_openid = Column(String(255), nullable=False, index=True)
    member_openids = Column(
        MutableList.as_mutable(JSON), nullable=False, default=list
    )
    invite_code = Column(String(64), nullable=False, index=True)
    quota = Column(Integer, nullable=False, default=5)
    items = relationship("Item", back_populates="team", cascade="all, delete-orphan")


class Item(TimestampMixin, Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_openid = Column(String(255), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    expire_date = Column(String(255), nullable=True)
    note = Column(String(1024), nullable=True)
    barcode = Column(String(255), nullable=True)
    product_image = Column(String(1024), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)

    deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(255), nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)

    team = relationship("Team", back_populates="items")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    # 使用 openid 作为主键，便于直接关联微信登录态
    openid = Column(String(255), primary_key=True)
    nickname = Column(String(255), nullable=True)
    phone_number = Column(String(32), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    reminder_days = Column(Integer, nullable=False, default=3)


class Product(TimestampMixin, Base):
    """商品库表 - 缓存条形码查询结果"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    brand = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    image = Column(String(1024), nullable=True)
    source = Column(String(50), nullable=True, comment='数据来源: local/openfoodfacts/upcitemdb/user')
    
    # 查询统计
    query_count = Column(Integer, default=0, nullable=False, comment='查询次数')
    last_queried_at = Column(DateTime(timezone=True), nullable=True, comment='最后查询时间')

