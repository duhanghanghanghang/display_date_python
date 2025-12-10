import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .models import Item, User
from .wechat import send_subscribe_message

logger = logging.getLogger("app.notifier")


def _parse_expire_date(date_str: Optional[str]) -> Optional[datetime]:
    """严格解析日期：YYYY-MM-DD 或 YYYY-MM-DD HH:MM，失败返回 None。"""
    if not date_str:
        return None
    fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def _find_due_items(db: Session) -> list[tuple[User, Item, datetime]]:
    now = datetime.now(timezone.utc)
    rows = (
        db.execute(
            select(Item, User)
            .join(User, User.openid == Item.owner_openid)
            .where(Item.deleted.is_(False), Item.notified_at.is_(None))
        )
        .all()
    )
    due = []
    for item, user in rows:
        expire_dt = _parse_expire_date(item.expire_date)
        if not expire_dt:
            continue
        reminder_days = user.reminder_days or 3
        if expire_dt.tzinfo is None:
            expire_dt = expire_dt.replace(tzinfo=timezone.utc)
        delta = expire_dt - now
        if delta <= timedelta(days=reminder_days):
            due.append((user, item, expire_dt))
    return due


async def notifier_loop():
    """每小时检查一次即将到期/已到期物品并推送订阅消息。"""
    if not settings.wechat_template_id:
        logger.warning("WECHAT_TEMPLATE_ID 未配置，跳过自动推送")
        return

    while True:
        try:
            with SessionLocal() as db:
                due_items = _find_due_items(db)
                if not due_items:
                    logger.info("notifier: no due items")
                for user, item, expire_dt in due_items:
                    # 订阅消息字段：thing1=物品名, date3=到期时间
                    data = {
                        "thing1": {"value": item.name[:20]},
                        "date3": {"value": expire_dt.strftime("%Y-%m-%d %H:%M")},
                    }
                    send_subscribe_message(
                        openid=user.openid,
                        template_id=settings.wechat_template_id,
                        data=data,
                        page="pages/index/index",
                        state="formal",
                    )
                    item.notified_at = datetime.now(timezone.utc)
                if due_items:
                    db.commit()
                if due_items:
                    logger.info("notifier: sent %d messages", len(due_items))
        except Exception as exc:
            logger.exception("notifier failed: %s", exc)

        await asyncio.sleep(3600)  # 1h

