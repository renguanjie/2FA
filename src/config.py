"""Application configuration management."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any


class Config:
    """Central configuration for the 2FA Authenticator app."""

    # App info
    APP_NAME = "2FA Authenticator"
    APP_VERSION = "0.1.0"

    # Database
    DB_NAME = "two_fa.db"

    # Encryption (Argon2id parameters)
    ARGON2_TIME_COST = 3          # iterations
    ARGON2_MEMORY_COST = 65536    # 64 MB in KB
    ARGON2_PARALLELISM = 4
    ARGON2_SALT_LENGTH = 16       # bytes

    # TOTP defaults (GitHub compatible)
    TOTP_ALGORITHM = "SHA1"
    TOTP_DIGITS = 6
    TOTP_PERIOD = 30              # seconds

    # Security
    AUTO_LOCK_SECONDS = 300       # 5 minutes
    CLIPBOARD_CLEAR_SECONDS = 30  # clear clipboard after 30s
    MAX_UNLOCK_ATTEMPTS = 5
    UNLOCK_DELAY_SECONDS = 30     # delay after max attempts

    # GitHub OAuth
    GITHUB_CLIENT_ID = ""         # Set via environment or settings
    GITHUB_CLIENT_SECRET = ""
    GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_API_BASE = "https://api.github.com"

    @staticmethod
    def get_data_dir() -> Path:
        """Get the application data directory.

        When packaged by Flet (mobile or desktop), Flet exposes a writable,
        persistent, app-specific storage directory via the ``FLET_APP_STORAGE_DATA``
        environment variable. On Android/iOS this is the *only* writable location,
        so it must take precedence over any platform-specific home-dir guess. The
        platform branches below are fallbacks for running un-packaged in dev.
        """
        import os

        storage = os.getenv("FLET_APP_STORAGE_DATA")
        if storage:
            return Path(storage)

        import platform
        system = platform.system()
        if system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "TwoFA"
        elif system == "Windows":
            return Path.home() / "AppData" / "Local" / "TwoFA"
        else:
            return Path.home() / ".two-fa"

    @classmethod
    def get_db_path(cls) -> Path:
        """Get the full database file path."""
        data_dir = cls.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / cls.DB_NAME

    @classmethod
    def get_settings_path(cls) -> Path:
        """Get the full settings file path."""
        data_dir = cls.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "settings.json"

    @classmethod
    def load_settings(cls) -> None:
        """Load persisted settings from disk if present."""
        path = cls.get_settings_path()
        if not path.exists():
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        cls.GITHUB_CLIENT_ID = str(data.get("github_client_id", cls.GITHUB_CLIENT_ID))
        cls.GITHUB_CLIENT_SECRET = str(
            data.get("github_client_secret", cls.GITHUB_CLIENT_SECRET)
        )
        cls.AUTO_LOCK_SECONDS = _int_setting(data, "auto_lock_seconds", cls.AUTO_LOCK_SECONDS)
        cls.CLIPBOARD_CLEAR_SECONDS = _int_setting(
            data, "clipboard_clear_seconds", cls.CLIPBOARD_CLEAR_SECONDS
        )

    @classmethod
    def save_settings(
        cls,
        *,
        github_client_id: str | None = None,
        github_client_secret: str | None = None,
        auto_lock_seconds: int | None = None,
        clipboard_clear_seconds: int | None = None,
    ) -> None:
        """Persist settings and update in-memory config values."""
        if github_client_id is not None:
            cls.GITHUB_CLIENT_ID = github_client_id
        if github_client_secret is not None:
            cls.GITHUB_CLIENT_SECRET = github_client_secret
        if auto_lock_seconds is not None:
            cls.AUTO_LOCK_SECONDS = int(auto_lock_seconds)
        if clipboard_clear_seconds is not None:
            cls.CLIPBOARD_CLEAR_SECONDS = int(clipboard_clear_seconds)

        data = {
            "github_client_id": cls.GITHUB_CLIENT_ID,
            "github_client_secret": cls.GITHUB_CLIENT_SECRET,
            "auto_lock_seconds": cls.AUTO_LOCK_SECONDS,
            "clipboard_clear_seconds": cls.CLIPBOARD_CLEAR_SECONDS,
        }
        cls.get_settings_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _int_setting(data: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(data.get(key, default))
    except (TypeError, ValueError):
        return default
