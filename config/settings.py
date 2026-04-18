import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Garena guest credentials
    garena_guest_uid: str = "your_guest_uid_here"
    garena_guest_token: str = "your_guest_token_here"

    # AES crypto constants
    # TO UPDATE: Extract 32-byte hex key and 16-byte hex IV from the latest
    # Free Fire APK using Frida or binary analysis of libil2cpp.so
    aes_key: str = "PLACEHOLDER_32_BYTE_HEX_KEY"
    aes_iv: str = "PLACEHOLDER_16_BYTE_HEX_IV"

    # Cache settings
    cache_ttl_seconds: int = 300
    cache_max_entries: int = 500

    # API settings
    ob_version: str = "OB53"
    server_port: int = 8080
    log_level: str = "INFO"

    # Rate limiting
    rate_limit_rpm: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
