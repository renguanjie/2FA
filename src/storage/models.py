"""SQLModel data models for the 2FA database."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Timezone-aware UTC now (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class VaultMeta(SQLModel, table=True):
    """Vault metadata (encryption params, verification token).

    Only one row should exist in this table.
    """

    __tablename__ = "vault_meta"

    id: int = Field(default=1, primary_key=True)
    salt: bytes                                  # Argon2 salt
    hash_params: str                             # JSON string of Argon2 params
    verification_token: bytes                    # Encrypted verification token
    version: int = 1                             # Schema version
    created_at: datetime = Field(default_factory=_utcnow)


class OTPAccountModel(SQLModel, table=True):
    """Encrypted OTP account entry."""

    __tablename__ = "otp_accounts"

    id: str = Field(primary_key=True)            # UUID
    issuer: str                                  # e.g. "GitHub"
    name: str                                    # e.g. "user@email.com"
    secret_encrypted: bytes                      # Fernet-encrypted secret
    otp_type: str = "totp"                       # "totp" or "hotp"
    algorithm: str = "SHA1"                      # SHA1/SHA256/SHA512
    digits: int = 6
    period: int = 30                             # TOTP interval (seconds)
    counter: int = 0                             # HOTP counter
    icon: Optional[str] = None                   # Icon identifier
    group: str = "Default"                       # Account group
    is_github: bool = False                      # GitHub account flag
    github_token_encrypted: Optional[bytes] = None  # Encrypted GitHub OAuth token
    notes: Optional[str] = None                  # User notes
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AppSecretModel(SQLModel, table=True):
    """Encrypted app-level secret such as OAuth connection tokens."""

    __tablename__ = "app_secrets"

    key: str = Field(primary_key=True)
    value_encrypted: bytes
    updated_at: datetime = Field(default_factory=_utcnow)
