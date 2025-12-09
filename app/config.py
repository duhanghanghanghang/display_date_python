import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


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


settings = Settings()

