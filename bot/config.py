import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot
    BOT_TOKEN: str = Field(default=os.getenv("BOT_TOKEN", "mock_bot_token"))
    BOT_USERNAME: str = Field(default=os.getenv("BOT_USERNAME", "everest_it_bot"))
    SUPERADMIN_IDS: str = Field(default=os.getenv("SUPERADMIN_IDS", "123456789"))

    # Webhook / Polling
    USE_WEBHOOK: bool = Field(default=False)
    WEBHOOK_URL: str = Field(default="")
    WEBHOOK_PATH: str = Field(default="/webhook")
    WEB_SERVER_HOST: str = Field(default="0.0.0.0")
    WEB_SERVER_PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: Optional[str] = Field(default=os.getenv("DATABASE_URL", None))
    SQLITE_DB_PATH: str = Field(default=os.getenv("SQLITE_DB_PATH", "data/everest_bot.db"))

    # Redis
    REDIS_URL: Optional[str] = Field(default=os.getenv("REDIS_URL", None))

    # AI
    ANTHROPIC_API_KEY: Optional[str] = Field(default=os.getenv("ANTHROPIC_API_KEY", None))
    GEMINI_API_KEY: Optional[str] = Field(default=os.getenv("GEMINI_API_KEY", None))
    AI_DEFAULT_PROVIDER: str = Field(default="claude")
    AI_DAILY_TOKEN_LIMIT: int = Field(default=500000)

    # Business Defaults
    DEFAULT_REFERRAL_POINTS: int = Field(default=10)
    DEFAULT_CHANNEL_ID: str = Field(default=os.getenv("DEFAULT_CHANNEL_ID", "-1001234567890"))
    DEFAULT_CHANNEL_LINK: str = Field(default=os.getenv("DEFAULT_CHANNEL_LINK", "https://t.me/everest_it_center"))
    DEFAULT_LANGUAGE: str = Field(default="uz")
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def superadmin_list(self) -> List[int]:
        if not self.SUPERADMIN_IDS:
            return []
        ids = []
        for x in self.SUPERADMIN_IDS.split(","):
            val = x.strip()
            if val.isdigit():
                ids.append(int(val))
        return ids

settings = Settings()
