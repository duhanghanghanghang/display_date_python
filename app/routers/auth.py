from fastapi import APIRouter

from ..auth import create_access_token, fake_wechat_code2session
from ..schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    openid = fake_wechat_code2session(payload.code)
    token = create_access_token(openid)
    return TokenResponse(token=token, openid=openid)

