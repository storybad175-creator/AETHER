from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings for Free Fire API.
    Loaded from environment variables or .env file.
    """
    # Garena guest credentials (extracted via MajorLogin)
    GARENA_GUEST_UID: str = Field(
        default="your_guest_uid_here",
        description="Garena Guest account UID for authentication"
    )
    GARENA_GUEST_TOKEN: str = Field(
        default="your_guest_token_here",
        description="Garena Guest account JWT token for authentication"
    )

    # AES crypto constants (64-char and 32-char hex strings)
    AES_KEY: str = Field(
        default="your_32_byte_hex_key_here",
        description="32-byte AES encryption key (hex encoded)"
    )
    AES_IV: str = Field(
        default="your_16_byte_hex_iv_here",
        description="16-byte AES IV (hex encoded)"
    )

    # Cache settings
    CACHE_TTL_SECONDS: int = Field(default=300, description="Time-to-live for cached player data")
    CACHE_MAX_ENTRIES: int = Field(default=500, description="Maximum number of entries in memory cache")

    # API settings
    OB_VERSION: str = Field(default="OB53", description="Current Free Fire OB version (e.g., OB53)")
    SERVER_PORT: int = Field(default=8080, description="Port to run the FastAPI server on")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # Rate limiting
    RATE_LIMIT_RPM: int = Field(default=30, description="Requests per minute limit per client IP")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
