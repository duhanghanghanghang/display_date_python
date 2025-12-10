from fastapi import APIRouter, Depends

from ..auth import get_current_openid
from ..schemas import MessageResponse, SubscribeSendRequest
from ..wechat import send_subscribe_message

router = APIRouter(prefix="/wechat", tags=["wechat"])


@router.post("/subscribe/send", response_model=MessageResponse)
def send_subscribe(payload: SubscribeSendRequest, openid: str = Depends(get_current_openid)):
    target_openid = payload.openid or openid
    send_subscribe_message(
        openid=target_openid,
        template_id=payload.template_id,
        data=payload.data,
        page=payload.page,
        state=payload.state or "formal",
        lang=payload.lang or "zh_CN",
    )
    return MessageResponse(message="sent")

