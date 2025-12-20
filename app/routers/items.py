from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_openid
from ..database import get_db
from ..models import Item, Team
from ..schemas import (
    ItemCreate,
    ItemOut,
    ItemUpdate,
    ItemsResponse,
    MessageResponse,
)
from ..wechat import send_subscribe_message
from ..config import settings

router = APIRouter(prefix="/items", tags=["items"])


def _parse_expire_date(date_str: Optional[str]) -> Optional[datetime]:
    """严格解析日期：YYYY-MM-DD 或 YYYY-MM-DD HH:MM。"""
    if not date_str:
        return None
    fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def normalize_team_id(team_id: Optional[str]) -> Optional[str]:
    if team_id is None or team_id == "":
        return None
    return team_id


def ensure_team_member(db: Session, team_id: str, openid: str) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if openid not in team.member_openids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No permission for this team"
        )
    return team


def ensure_item_permission(db: Session, item: Item, openid: str) -> None:
    if item.team_id:
        ensure_team_member(db, item.team_id, openid)
    else:
        if item.owner_openid != openid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No permission for this item"
            )


@router.get("", response_model=ItemsResponse)
def list_items(
    team_id: Optional[str] = Query(default=None, alias="teamId"),
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team_id = normalize_team_id(team_id)
    if team_id:
        ensure_team_member(db, team_id, openid)
        stmt = (
            select(Item)
            .where(Item.team_id == team_id, Item.deleted.is_(False))
            .order_by(Item.updated_at.desc())
        )
    else:
        stmt = (
            select(Item)
            .where(
                Item.owner_openid == openid,
                Item.team_id.is_(None),
                Item.deleted.is_(False),
            )
            .order_by(Item.updated_at.desc())
        )
    items = db.scalars(stmt).all()
    return ItemsResponse(items=items)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    item = db.get(Item, item_id)
    if not item or item.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    ensure_item_permission(db, item, openid)
    return item


@router.post("/notify", response_model=MessageResponse)
def notify_items(
    item_ids: list[str],
    send: bool = True,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    if not item_ids:
        return MessageResponse(message="no items")
    items = (
        db.execute(
            select(Item).where(
                Item.id.in_(item_ids),
                Item.owner_openid == openid,
                Item.deleted.is_(False),
            )
        )
        .scalars()
        .all()
    )
    if not items:
        return MessageResponse(message="no items")

    now = datetime.now(timezone.utc)
    sent = 0
    for item in items:
        item.notified_at = now
        if send and settings.wechat_template_id:
            expire_dt = _parse_expire_date(item.expire_date)
            if not expire_dt:
                continue
            data = {
                "thing1": {"value": item.name[:20]},
                "date3": {"value": expire_dt.strftime("%Y-%m-%d %H:%M")},
            }
            send_subscribe_message(
                openid=openid,
                template_id=settings.wechat_template_id,
                data=data,
                page="pages/index/index",
                state="formal",
            )
            sent += 1
    db.commit()
    return MessageResponse(message=f"notified {len(items)}, sent {sent}")



@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    team_id = normalize_team_id(payload.team_id)
    if team_id:
        ensure_team_member(db, team_id, openid)

    now = datetime.now(timezone.utc)
    existing = db.scalar(
        select(Item).where(
            Item.owner_openid == openid,
            Item.team_id == team_id,
            Item.name == payload.name,
            Item.deleted.is_(True),
        )
    )

    if existing:
        # 恢复已删除的记录，不使用 by_alias 以确保字段名匹配数据库
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "team_id":
                continue
            if hasattr(existing, field):
            setattr(existing, field, value)
        existing.deleted = False
        existing.deleted_at = None
        existing.deleted_by = None
        existing.updated_at = now
        item = existing
    else:
        item = Item(
            owner_openid=openid,
            team_id=team_id,
            name=payload.name,
            category=payload.category,
            expire_date=payload.expire_date,
            note=payload.note,
            barcode=payload.barcode,
            product_image=payload.product_image,
            quantity=payload.quantity if payload.quantity is not None else 1,
            deleted=False,
            created_at=now,
            updated_at=now,
        )
        db.add(item)

    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(
    item_id: str,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    item = db.get(Item, item_id)
    if not item or item.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    ensure_item_permission(db, item, openid)
    
    # 使用 exclude_unset=True 只更新提交的字段
    # 不使用 by_alias，因为数据库字段名是 product_image 而不是 productImage
    update_data = payload.model_dump(exclude_unset=True)
    
    # 字段名映射：前端别名 -> 数据库字段名
    field_mapping = {
        'teamId': 'team_id',
        'productImage': 'product_image',
        'expireDate': 'expire_date'
    }
    
    for field, value in update_data.items():
        # 跳过 team_id（由前端通过 teamId 传递，但不应更新到 item）
        if field == 'team_id':
            continue
        # 使用映射后的字段名
        db_field = field_mapping.get(field, field)
        if hasattr(item, db_field):
            setattr(item, db_field, value)
    
    item.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/delete", response_model=MessageResponse)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    ensure_item_permission(db, item, openid)

    now = datetime.now(timezone.utc)
    item.deleted = True
    item.deleted_at = now
    item.deleted_by = openid
    item.updated_at = now

    db.commit()
    return MessageResponse()


@router.patch("/{item_id}/unnotify", response_model=MessageResponse)
def unnotify_item(
    item_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    item = db.get(Item, item_id)
    if not item or item.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    ensure_item_permission(db, item, openid)
    item.notified_at = None
    db.commit()
    return MessageResponse(message="unnotified")

