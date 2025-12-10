from datetime import datetime, timezone
from typing import Any, Dict

import logging
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

bearer_scheme = HTTPBearer()
logger = logging.getLogger("app.auth")


def create_access_token(openid: str) -> str:
    expire_at = datetime.now(timezone.utc) + settings.jwt_expires
    to_encode = {"sub": openid, "exp": expire_at}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_openid(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        openid: str | None = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    if not openid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return openid


def fake_wechat_code2session(code: str) -> str:
    """调用微信官方 code2Session 获取 openid。"""
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="code is required"
        )
    if not settings.wechat_appid or not settings.wechat_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WeChat appid/secret not configured",
        )

    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    try:
        resp = requests.get(
            "https://api.weixin.qq.com/sns/jscode2session", params=params, timeout=5
        )
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
    except Exception as exc:  # pragma: no cover - 网络异常直接报出
        logger.warning("code2session request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to call WeChat code2session",
        )

    errcode = data.get("errcode")
    if errcode:
        errmsg = data.get("errmsg", "unknown error")
        logger.info("code2session error errcode=%s errmsg=%s", errcode, errmsg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"WeChat error: {errmsg}",
        )

    openid = data.get("openid")
    if not openid:
        logger.info("code2session missing openid: %s", data)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="WeChat openid missing"
        )
    logger.info("code2session ok openid=%s", openid)
    return openid

