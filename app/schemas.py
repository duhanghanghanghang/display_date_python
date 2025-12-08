from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenResponse(BaseModel):
    token: str
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
    product_image: Optional[str] = None
    team_id: Optional[str] = Field(default=None, alias="teamId")
    model_config = ConfigDict(populate_by_name=True)


class ItemCreate(ItemBase):
    name: str


class ItemUpdate(ItemBase):
    pass


class ItemOut(ItemBase):
    id: str
    owner_openid: str
    deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[str]
    add_date: Optional[datetime]
    update_date: Optional[datetime]
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

