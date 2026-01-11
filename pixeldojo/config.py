"""
Configuration management for PixelDojo.

Supports:
- Environment variables
- Configuration files (XDG-compliant paths)
- Secure API key storage with keyring
- Runtime configuration
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import keyring
from platformdirs import user_cache_dir, user_config_dir, user_data_dir
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Application identifiers
APP_NAME = "pixeldojo"
APP_AUTHOR = "pixeldojo"
KEYRING_SERVICE = "pixeldojo-api"
KEYRING_USERNAME = "api_key"


def get_config_dir() -> Path:
    """Get XDG-compliant config directory."""
    return Path(user_config_dir(APP_NAME, APP_AUTHOR))


def get_data_dir() -> Path:
    """Get XDG-compliant data directory."""
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_cache_dir() -> Path:
    """Get XDG-compliant cache directory."""
    return Path(user_cache_dir(APP_NAME, APP_AUTHOR))


def ensure_directories() -> None:
    """Ensure all application directories exist."""
    for dir_func in (get_config_dir, get_data_dir, get_cache_dir):
        dir_path = dir_func()
        dir_path.mkdir(parents=True, exist_ok=True)


class Config(BaseSettings):
    """
    Application configuration with environment variable support.

    Environment variables:
        PIXELDOJO_API_KEY: API authentication key
        PIXELDOJO_API_URL: Base URL for API (default: https://pixeldojo.ai/api/v1)
        PIXELDOJO_TIMEOUT: Request timeout in seconds (default: 120)
        PIXELDOJO_MAX_RETRIES: Maximum retry attempts (default: 3)
        PIXELDOJO_DEBUG: Enable debug mode (default: false)
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXELDOJO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Settings
    api_key: str = Field(
        default="",
        description="PixelDojo API key",
    )
    api_url: str = Field(
        default="https://pixeldojo.ai/api/v1",
        description="Base URL for PixelDojo API",
    )

    # Request Settings
    timeout: float = Field(
        default=120.0,
        ge=1.0,
        le=600.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed requests",
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=30.0,
        description="Initial delay between retries (exponential backoff)",
    )

    # Connection Settings
    max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent connections",
    )

    # Application Settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging",
    )
    default_model: str = Field(
        default="flux-pro",
        description="Default model for generation",
    )
    default_aspect_ratio: str = Field(
        default="1:1",
        description="Default aspect ratio for generation",
    )
    default_num_outputs: int = Field(
        default=1,
        ge=1,
        le=4,
        description="Default number of outputs",
    )

    # Storage Settings
    download_dir: Path = Field(
        default_factory=lambda: Path.home() / "Pictures" / "PixelDojo",
        description="Directory for downloaded images",
    )
    history_enabled: bool = Field(
        default=True,
        description="Enable generation history",
    )
    max_history: int = Field(
        default=1000,
        ge=0,
        description="Maximum history entries to keep",
    )

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Ensure API URL doesn't have trailing slash."""
        return v.rstrip("/")

    @model_validator(mode="after")
    def load_keyring_api_key(self) -> Config:
        """Load API key from keyring if not set."""
        if not self.api_key:
            try:
                stored_key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
                if stored_key:
                    object.__setattr__(self, "api_key", stored_key)
            except Exception:
                pass  # Keyring not available or empty
        return self

    def save_api_key(self, api_key: str) -> None:
        """Save API key to secure keyring storage."""
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, api_key)
        object.__setattr__(self, "api_key", api_key)

    def delete_api_key(self) -> None:
        """Remove API key from keyring storage."""
        import contextlib
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        object.__setattr__(self, "api_key", "")

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def ensure_download_dir(self) -> Path:
        """Ensure download directory exists and return path."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        return self.download_dir

    def get_history_path(self) -> Path:
        """Get path to history database."""
        return get_data_dir() / "history.json"

    def get_log_path(self) -> Path:
        """Get path to log file."""
        return get_data_dir() / "pixeldojo.log"


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached application configuration singleton."""
    ensure_directories()
    return Config()


def reload_config() -> Config:
    """Force reload configuration (clears cache)."""
    get_config.cache_clear()
    return get_config()
