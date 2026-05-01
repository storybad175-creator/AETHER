from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings for Free Fire API.
    Loaded from environment variables or .env file.
    """
    # Garena guest credentials
    # Obtain by following the guest JWT extraction guide in README.md
    GARENA_GUEST_UID: str = Field(default="your_guest_uid_here")
    GARENA_GUEST_TOKEN: str = Field(default="your_guest_token_here")

    # AES crypto constants (Hex strings)
    # Community-extracted from Free Fire APK binary analysis (e.g. libil2cpp.so)
    # Update these values in your .env file.
    # AES_KEY must be a 64-character hex string (32 bytes).
    # AES_IV must be a 32-character hex string (16 bytes).
    AES_KEY: str = Field(default="your_32_byte_hex_key_here")
    AES_IV: str = Field(default="your_16_byte_hex_iv_here")

    # Cache settings
    CACHE_TTL_SECONDS: int = Field(default=300)
    CACHE_MAX_ENTRIES: int = Field(default=500)

    # API settings
    OB_VERSION: str = Field(default="OB53")
    SERVER_PORT: int = Field(default=8080)
    LOG_LEVEL: str = Field(default="INFO")

    # Rate limiting
    RATE_LIMIT_RPM: int = Field(default=30)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
