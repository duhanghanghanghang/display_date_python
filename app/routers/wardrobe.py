"""衣柜管理 API 路由"""
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..auth import get_current_openid
from ..database import get_db
from ..models import WardrobeCategory, WardrobeItem, WardrobeOutfit
from ..schemas import (
    MessageResponse,
    WardrobeCategoryCreate,
    WardrobeCategoryOut,
    WardrobeCategoriesResponse,
    WardrobeCategoryUpdate,
    WardrobeItemCreate,
    WardrobeItemOut,
    WardrobeItemsResponse,
    WardrobeItemUpdate,
    WardrobeOutfitCreate,
    WardrobeOutfitOut,
    WardrobeOutfitsResponse,
    WardrobeOutfitUpdate,
)

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


# ============ Categories APIs ============

@router.get("/categories", response_model=WardrobeCategoriesResponse)
def get_categories(
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """获取用户的所有衣服分类，并统计每个分类下的衣服数量"""
    categories = db.scalars(
        select(WardrobeCategory)
        .where(WardrobeCategory.owner_openid == openid)
        .order_by(WardrobeCategory.sort_order, WardrobeCategory.created_at)
    ).all()
    
    # 统计每个分类下的衣服数量
    result = []
    for cat in categories:
        count = db.scalar(
            select(func.count(WardrobeItem.id))
            .where(
                WardrobeItem.category_id == cat.id,
                WardrobeItem.deleted == False
            )
        ) or 0
        
        cat_dict = {
            "id": cat.id,
            "name": cat.name,
            "sort_order": cat.sort_order,
            "owner_openid": cat.owner_openid,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "count": count
        }
        result.append(WardrobeCategoryOut(**cat_dict))
    
    return WardrobeCategoriesResponse(categories=result)


@router.post("/categories", response_model=WardrobeCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: WardrobeCategoryCreate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """创建新的衣服分类"""
    # 检查是否重名
    existing = db.scalar(
        select(WardrobeCategory).where(
            WardrobeCategory.owner_openid == openid,
            WardrobeCategory.name == payload.name
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分类名称已存在"
        )
    
    category = WardrobeCategory(
        id=str(uuid4()),
        owner_openid=openid,
        name=payload.name,
        sort_order=payload.sort_order or 0
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    cat_dict = {**category.__dict__, "count": 0}
    return WardrobeCategoryOut(**cat_dict)


@router.patch("/categories/{category_id}", response_model=WardrobeCategoryOut)
def update_category(
    category_id: str,
    payload: WardrobeCategoryUpdate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """更新分类信息"""
    category = db.get(WardrobeCategory, category_id)
    if not category or category.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(category, field):
            setattr(category, field, value)
    
    category.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(category)
    
    # 统计数量
    count = db.scalar(
        select(func.count(WardrobeItem.id))
        .where(WardrobeItem.category_id == category_id, WardrobeItem.deleted == False)
    ) or 0
    
    cat_dict = {**category.__dict__, "count": count}
    return WardrobeCategoryOut(**cat_dict)


@router.delete("/categories/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """删除分类（会级联删除该分类下的所有衣服）"""
    category = db.get(WardrobeCategory, category_id)
    if not category or category.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    
    db.delete(category)
    db.commit()
    return MessageResponse(message="删除成功")


# ============ Items APIs ============

@router.get("/items", response_model=WardrobeItemsResponse)
def get_items(
    category_id: str = None,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """获取衣服列表，可按分类筛选"""
    query = select(WardrobeItem).where(
        WardrobeItem.owner_openid == openid,
        WardrobeItem.deleted == False
    )
    
    if category_id:
        query = query.where(WardrobeItem.category_id == category_id)
    
    query = query.order_by(WardrobeItem.created_at.desc())
    items = db.scalars(query).all()
    
    # 附加分类名称
    result = []
    for item in items:
        category = db.get(WardrobeCategory, item.category_id)
        item_dict = {**item.__dict__, "category_name": category.name if category else "未知"}
        result.append(WardrobeItemOut(**item_dict))
    
    return WardrobeItemsResponse(items=result)


@router.post("/items", response_model=WardrobeItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: WardrobeItemCreate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """创建新衣服"""
    # 验证分类是否存在且属于当前用户
    category = db.get(WardrobeCategory, payload.category_id)
    if not category or category.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")
    
    item = WardrobeItem(
        id=str(uuid4()),
        owner_openid=openid,
        category_id=payload.category_id,
        name=payload.name,
        color=payload.color,
        size=payload.size,
        season=payload.season,
        brand=payload.brand,
        price=payload.price,
        purchase_date=payload.purchase_date,
        image_url=payload.image_url,
        note=payload.note,
        deleted=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    item_dict = {**item.__dict__, "category_name": category.name}
    return WardrobeItemOut(**item_dict)


@router.patch("/items/{item_id}", response_model=WardrobeItemOut)
def update_item(
    item_id: str,
    payload: WardrobeItemUpdate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """更新衣服信息"""
    item = db.get(WardrobeItem, item_id)
    if not item or item.owner_openid != openid or item.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="衣服不存在")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)
    
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    
    category = db.get(WardrobeCategory, item.category_id)
    item_dict = {**item.__dict__, "category_name": category.name if category else "未知"}
    return WardrobeItemOut(**item_dict)


@router.delete("/items/{item_id}", response_model=MessageResponse)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """删除衣服（软删除）"""
    item = db.get(WardrobeItem, item_id)
    if not item or item.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="衣服不存在")
    
    item.deleted = True
    item.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return MessageResponse(message="删除成功")


# ============ Outfits APIs ============

@router.get("/outfits", response_model=WardrobeOutfitsResponse)
def get_outfits(
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """获取所有搭配方案"""
    outfits = db.scalars(
        select(WardrobeOutfit)
        .where(WardrobeOutfit.owner_openid == openid)
        .order_by(WardrobeOutfit.created_at.desc())
    ).all()
    
    return WardrobeOutfitsResponse(outfits=outfits)


@router.post("/outfits", response_model=WardrobeOutfitOut, status_code=status.HTTP_201_CREATED)
def create_outfit(
    payload: WardrobeOutfitCreate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """创建新搭配方案"""
    outfit = WardrobeOutfit(
        id=str(uuid4()),
        owner_openid=openid,
        name=payload.name,
        items=payload.items,
        occasion=payload.occasion,
        season=payload.season,
        image_url=payload.image_url
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    
    return WardrobeOutfitOut(**outfit.__dict__)


@router.patch("/outfits/{outfit_id}", response_model=WardrobeOutfitOut)
def update_outfit(
    outfit_id: str,
    payload: WardrobeOutfitUpdate,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """更新搭配方案"""
    outfit = db.get(WardrobeOutfit, outfit_id)
    if not outfit or outfit.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="搭配方案不存在")
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(outfit, field):
            setattr(outfit, field, value)
    
    outfit.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(outfit)
    
    return WardrobeOutfitOut(**outfit.__dict__)


@router.delete("/outfits/{outfit_id}", response_model=MessageResponse)
def delete_outfit(
    outfit_id: str,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    """删除搭配方案"""
    outfit = db.get(WardrobeOutfit, outfit_id)
    if not outfit or outfit.owner_openid != openid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="搭配方案不存在")
    
    db.delete(outfit)
    db.commit()
    return MessageResponse(message="删除成功")
