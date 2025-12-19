import os
from datetime import timedelta

from .env_loader import load_env

load_env()


class Settings:
    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://appuser:apppassword@localhost:3306/display_date",
        )
        self.jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
        self.jwt_algorithm: str = "HS256"
        self.jwt_expires: timedelta = timedelta(
            minutes=int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))
        )
        self.invite_code_length: int = int(os.getenv("INVITE_CODE_LENGTH", "8"))
        self.wechat_appid: str | None = os.getenv("WECHAT_APPID")
        self.wechat_secret: str | None = os.getenv("WECHAT_SECRET")
        self.wechat_template_id: str | None = os.getenv("WECHAT_TEMPLATE_ID")
        # GitHub Webhook 配置
        self.github_webhook_secret: str | None = os.getenv("GITHUB_WEBHOOK_SECRET")


settings = Settings()

