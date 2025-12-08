from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

bearer_scheme = HTTPBearer()


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
    """
    简化版 code2Session。真实环境下需调用微信接口。
    这里直接返回 code 作为 openid，便于前后端联调。
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="code is required"
        )
    return code

