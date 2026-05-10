from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings for Free Fire API.
    Loaded from environment variables or .env file.
    """
    # Garena guest credentials
    # Required for the MajorLogin authentication flow.
    GARENA_GUEST_UID: str = Field(
        default="your_guest_uid_here",
        description="Garena Guest UID captured from MajorLogin request"
    )
    GARENA_GUEST_TOKEN: str = Field(
        default="your_guest_token_here",
        description="Garena Guest Token captured from MajorLogin request"
    )

    # AES crypto constants (Hex strings)
    # These are used for wire-protocol encryption/decryption.
    # Extracted from libil2cpp.so or libunity.so via binary analysis.
    AES_KEY: str = Field(
        default="your_32_byte_hex_key_here",
        description="32-byte hex string for AES-256-CBC"
    )
    AES_IV: str = Field(
        default="your_16_byte_hex_iv_here",
        description="16-byte hex string for AES-256-CBC IV"
    )

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
