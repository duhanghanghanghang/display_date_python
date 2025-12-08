from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_openid
from ..database import get_db
from ..models import Item, Team
from ..schemas import ItemCreate, ItemOut, ItemUpdate, ItemsResponse, MessageResponse

router = APIRouter(prefix="/items", tags=["items"])


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
            .order_by(Item.update_date.desc())
        )
    else:
        stmt = (
            select(Item)
            .where(
                Item.owner_openid == openid,
                Item.team_id.is_(None),
                Item.deleted.is_(False),
            )
            .order_by(Item.update_date.desc())
        )
    items = db.scalars(stmt).all()
    return ItemsResponse(items=items)


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
        update_data = payload.model_dump(exclude_unset=True, by_alias=True)
        for field, value in update_data.items():
            if field == "teamId":
                continue
            setattr(existing, field, value)
        existing.deleted = False
        existing.deleted_at = None
        existing.deleted_by = None
        existing.update_date = now
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
            deleted=False,
            add_date=now,
            update_date=now,
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
    update_data = payload.model_dump(exclude_unset=True, by_alias=True)
    for field, value in update_data.items():
        if field == "teamId":
            continue
        setattr(item, field, value)
    item.update_date = datetime.now(timezone.utc)

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
    item.update_date = now

    db.commit()
    return MessageResponse()

