from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GARENA_GUEST_UID: str = "your_guest_uid_here"
    GARENA_GUEST_TOKEN: str = "your_guest_token_here"

    AES_KEY: str = "your_32_byte_hex_key_here"
    AES_IV: str = "your_16_byte_hex_iv_here"

    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 500

    OB_VERSION: str = "OB53"
    SERVER_PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    RATE_LIMIT_RPM: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
