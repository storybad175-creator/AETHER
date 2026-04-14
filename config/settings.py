from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GARENA_GUEST_UID: str = "guest_uid"
    GARENA_GUEST_TOKEN: str = "guest_token"

    AES_KEY: str = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    AES_IV: str = "000102030405060708090a0b0c0d0e0f"

    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 500

    OB_VERSION: str = "OB53"
    SERVER_PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    RATE_LIMIT_RPM: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
