from typing import Any, Dict

import logging
import requests
from fastapi import Header, HTTPException, status

from .config import settings

logger = logging.getLogger("app.auth")


def get_current_openid(
    x_openid: str = Header(None, alias="X-OpenId"),
    openid: str = Header(None, alias="openid"),
) -> str:
    """
    从请求头中获取 openid。
    支持两种方式：X-OpenId 或 openid
    """
    user_openid = x_openid or openid
    if not user_openid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing openid in header",
        )
    return user_openid


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

