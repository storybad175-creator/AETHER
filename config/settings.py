from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Garena guest credentials
    GARENA_GUEST_UID: str = "your_guest_uid_here"
    GARENA_GUEST_TOKEN: str = "your_guest_token_here"

    # AES crypto constants
    AES_KEY: str = "your_32_byte_hex_key_here"
    AES_IV: str = "your_16_byte_hex_iv_here"

    # Cache settings
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 500

    # API settings
    OB_VERSION: str = "OB53"
    SERVER_PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    # Rate limiting
    RATE_LIMIT_RPM: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
