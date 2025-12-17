from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..auth import fake_wechat_code2session, get_current_openid
from ..database import get_db
from ..models import User
from ..schemas import (
    LoginRequest,
    LoginResponse,
    UpdateUserProfile,
    UserProfile,
)

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """
    微信小程序登录，使用 code 换取 openid。
    客户端需要保存 openid，并在后续请求的 header 中携带（X-OpenId 或 openid）。
    """
    openid = fake_wechat_code2session(payload.code)
    return LoginResponse(openid=openid)


@router.get("/me", response_model=UserProfile)
@router.get("/settings/me", response_model=UserProfile)
def get_me(
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    # 若用户不存在则以默认值创建，避免客户端拿不到用户资料
    user = db.get(User, openid)
    if not user:
        user = User(
            openid=openid,
            nickname=f"微信用户{openid[-4:]}",
            phone_number=None,
            avatar_url=None,
            reminder_days=3,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.patch("/me", response_model=UserProfile)
@router.patch("/settings/me", response_model=UserProfile)
@router.put("/me", response_model=UserProfile)
@router.put("/settings/me", response_model=UserProfile)
def update_me(
    payload: UpdateUserProfile,
    db: Session = Depends(get_db),
    openid: str = Depends(get_current_openid),
):
    user = db.get(User, openid)
    if not user:
        user = User(
            openid=openid,
            nickname=f"微信用户{openid[-4:]}",
            phone_number=None,
            avatar_url=None,
            reminder_days=3,
        )
        db.add(user)

    update_data = payload.model_dump(exclude_none=True, by_alias=True)
    for field, value in update_data.items():
        if field == "phoneNumber":
            setattr(user, "phone_number", value)
        elif field == "avatarUrl":
            setattr(user, "avatar_url", value)
        elif field == "reminderDays":
            setattr(user, "reminder_days", int(value))
        else:
            setattr(user, field, value)

    # 无论字段是否变更，强制更新时间戳
    user.updated_at = func.now()

    db.commit()
    db.refresh(user)
    return user

