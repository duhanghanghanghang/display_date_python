from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import logging
import requests
from fastapi import HTTPException, status

from .config import settings

logger = logging.getLogger("app.wechat")

_token_cache: Dict[str, Any] = {"token": None, "expire_at": None}


def _fetch_access_token() -> str:
    if not settings.wechat_appid or not settings.wechat_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WeChat appid/secret not configured",
        )
    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={settings.wechat_appid}&secret={settings.wechat_secret}"
    )
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    if "errcode" in data and data["errcode"] != 0:
        logger.error("get access_token failed: %s", data)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WeChat token error: {data.get('errmsg', 'unknown')}",
        )
    token = data.get("access_token")
    expires_in = int(data.get("expires_in", 7000))
    _token_cache["token"] = token
    _token_cache["expire_at"] = datetime.now(timezone.utc) + timedelta(
        seconds=expires_in - 60
    )
    return token


def get_access_token() -> str:
    token = _token_cache.get("token")
    expire_at: Optional[datetime] = _token_cache.get("expire_at")
    if token and expire_at and expire_at > datetime.now(timezone.utc):
        return token
    return _fetch_access_token()


def send_subscribe_message(
    openid: str,
    template_id: str,
    data: Dict[str, Any],
    page: Optional[str] = None,
    state: str = "formal",
    lang: str = "zh_CN",
) -> Dict[str, Any]:
    """调用微信订阅消息发送接口。"""
    if not openid or not template_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="openid and templateId are required",
        )

    access_token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data,
        "miniprogram_state": state,
        "lang": lang,
    }
    if page:
        payload["page"] = page

    resp = requests.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    result = resp.json()
    if result.get("errcode") != 0:
        logger.error("subscribe send failed: %s", result)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WeChat send error: {result.get('errmsg', 'unknown')}",
        )
    return result

