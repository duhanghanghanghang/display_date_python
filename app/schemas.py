from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LoginResponse(BaseModel):
    openid: str


class LoginRequest(BaseModel):
    code: str


class MessageResponse(BaseModel):
    message: str = "ok"


class ItemBase(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    expire_date: Optional[str] = None
    note: Optional[str] = None
    barcode: Optional[str] = None
    product_image: Optional[str] = Field(default=None, alias="productImage")
    quantity: Optional[int] = 1
    team_id: Optional[str] = Field(default=None, alias="teamId")
    model_config = ConfigDict(populate_by_name=True)


class ItemCreate(ItemBase):
    name: str


class ItemUpdate(ItemBase):
    pass


class ItemOut(ItemBase):
    id: str
    owner_openid: str
    quantity: int = 1
    deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]
    created_at: Optional[datetime] = Field(default=None, alias="addDate")
    updated_at: Optional[datetime] = Field(default=None, alias="updateDate")
    notified_at: Optional[datetime] = Field(default=None, alias="notifiedAt")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ItemsResponse(BaseModel):
    items: List[ItemOut]


class TeamBase(BaseModel):
    name: str
    invite_code: Optional[str] = Field(default=None, alias="inviteCode")
    quota: Optional[int] = 5
    model_config = ConfigDict(populate_by_name=True)


class TeamCreate(TeamBase):
    pass


class TeamOut(BaseModel):
    id: str
    name: str
    owner_openid: str
    member_openids: List[str]
    invite_code: str
    quota: int
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TeamsResponse(BaseModel):
    teams: List[TeamOut]


class TeamResponse(BaseModel):
    team: TeamOut


class JoinTeamRequest(BaseModel):
    invite_code: str = Field(alias="inviteCode")
    model_config = ConfigDict(populate_by_name=True)


class RenameTeamRequest(BaseModel):
    name: str


class RemoveMemberRequest(BaseModel):
    member_openid: str = Field(alias="memberOpenId")
    model_config = ConfigDict(populate_by_name=True)


class UserProfile(BaseModel):
    openid: str
    nickname: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    reminder_days: int = Field(default=3, alias="reminderDays")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UpdateUserProfile(BaseModel):
    nickname: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, alias="phoneNumber")
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    reminder_days: Optional[int] = Field(default=None, alias="reminderDays")
    model_config = ConfigDict(populate_by_name=True)


class SubscribeSendRequest(BaseModel):
    """发送订阅消息请求体。"""

    template_id: str = Field(alias="templateId")
    data: dict
    page: Optional[str] = None  # 小程序跳转页面，如不需要可不传
    state: Optional[str] = Field(
        default="formal", alias="miniprogramState"
    )  # formal / trial / develop
    lang: Optional[str] = "zh_CN"
    openid: Optional[str] = None  # 如不传则使用当前登录态的 openid
    model_config = ConfigDict(populate_by_name=True)


# ============ Wardrobe Category schemas ============
class WardrobeCategoryBase(BaseModel):
    name: str
    sort_order: Optional[int] = Field(default=0, alias="sortOrder")
    model_config = ConfigDict(populate_by_name=True)


class WardrobeCategoryCreate(WardrobeCategoryBase):
    pass


class WardrobeCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    model_config = ConfigDict(populate_by_name=True)


class WardrobeCategoryOut(WardrobeCategoryBase):
    id: str
    owner_openid: str = Field(alias="ownerOpenid")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    count: Optional[int] = 0  # 统计该分类下的衣服数量
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WardrobeCategoriesResponse(BaseModel):
    categories: List[WardrobeCategoryOut]


# ============ Wardrobe Item schemas ============
class WardrobeItemBase(BaseModel):
    category_id: str = Field(alias="categoryId")
    name: str
    color: Optional[str] = None
    size: Optional[str] = None
    season: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = None
    purchase_date: Optional[date] = Field(default=None, alias="purchaseDate")
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    note: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)


class WardrobeItemCreate(WardrobeItemBase):
    pass


class WardrobeItemUpdate(BaseModel):
    category_id: Optional[str] = Field(default=None, alias="categoryId")
    name: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    season: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = None
    purchase_date: Optional[date] = Field(default=None, alias="purchaseDate")
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    note: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)


class WardrobeItemOut(WardrobeItemBase):
    id: str
    owner_openid: str = Field(alias="ownerOpenid")
    deleted: bool
    deleted_at: Optional[datetime] = Field(default=None, alias="deletedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    category_name: Optional[str] = Field(default=None, alias="categoryName")  # 分类名称
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WardrobeItemsResponse(BaseModel):
    items: List[WardrobeItemOut]


# ============ Wardrobe Outfit schemas ============
class WardrobeOutfitBase(BaseModel):
    name: str
    items: dict  # {"top": "item_id", "bottom": "item_id", ...}
    occasion: Optional[str] = None
    season: Optional[str] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    model_config = ConfigDict(populate_by_name=True)


class WardrobeOutfitCreate(WardrobeOutfitBase):
    pass


class WardrobeOutfitUpdate(BaseModel):
    name: Optional[str] = None
    items: Optional[dict] = None
    occasion: Optional[str] = None
    season: Optional[str] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    model_config = ConfigDict(populate_by_name=True)


class WardrobeOutfitOut(WardrobeOutfitBase):
    id: str
    owner_openid: str = Field(alias="ownerOpenid")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WardrobeOutfitsResponse(BaseModel):
    outfits: List[WardrobeOutfitOut]

