"""Encrypted vault for managing OTP accounts.

Provides a secure storage layer that encrypts all sensitive data
(secrets, tokens) using a master password-derived key.

Reference: Aegis Authenticator's vault architecture.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from sqlmodel import select

from src.core.crypto import (
    KeyDerivationParams,
    create_fernet,
    decrypt,
    derive_key,
    encrypt,
    generate_verification_token,
    verify_master_key,
)
from src.core.otp import OTPAccount, OTPType, Algorithm
from src.core.uri_parser import parse_otpauth_uri, to_provisioning_uri


class VaultError(Exception):
    """Base vault exception."""


class VaultLockedError(VaultError):
    """Raised when accessing a locked vault."""


class VaultUnlockError(VaultError):
    """Raised when unlock fails (wrong password)."""


class Vault:
    """Encrypted vault for OTP accounts.

    Architecture:
    - Master key derived from user password via Argon2id
    - Each account's secret encrypted independently with Fernet
    - Verification token to validate password on unlock

    Usage:
        vault = Vault(db_path)
        vault.create("my_password")       # First time
        vault.unlock("my_password")       # Subsequent sessions
        vault.add_account(account)         # Add OTP account
        accounts = vault.get_all_accounts()
        vault.lock()                       # Clear key from memory
    """

    def __init__(self, db_path: Path):
        """Initialize vault with a database path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._fernet: Optional[Fernet] = None
        self._params: Optional[KeyDerivationParams] = None

        # Ensure database tables exist
        from src.storage.database import init_db
        init_db(db_path)

    @property
    def is_unlocked(self) -> bool:
        """Check if the vault is currently unlocked."""
        return self._fernet is not None

    def _ensure_unlocked(self) -> Fernet:
        """Ensure vault is unlocked and return the Fernet instance."""
        if not self.is_unlocked:
            raise VaultLockedError("Vault is locked. Call unlock() first.")
        return self._fernet

    def _load_meta(self) -> Optional[dict]:
        """Load vault metadata from the database."""
        from src.storage.database import get_session
        from src.storage.models import VaultMeta

        with get_session(self._db_path) as session:
            meta = session.exec(select(VaultMeta)).first()
            if meta is None:
                return None
            return {
                "hash_params": json.loads(meta.hash_params),
                "verification_token": meta.verification_token,
                "version": meta.version,
            }

    def _save_meta(self, params: KeyDerivationParams, token: bytes) -> None:
        """Save vault metadata to the database."""
        from src.storage.database import get_session
        from src.storage.models import VaultMeta

        with get_session(self._db_path) as session:
            existing = session.exec(select(VaultMeta)).first()
            if existing:
                existing.salt = params.salt
                existing.hash_params = json.dumps(params.to_dict())
                existing.verification_token = token
            else:
                meta = VaultMeta(
                    salt=params.salt,
                    hash_params=json.dumps(params.to_dict()),
                    verification_token=token,
                    version=1,
                )
                session.add(meta)
            session.commit()

    def create(self, password: str) -> None:
        """Create a new vault with the given master password.

        Args:
            password: The master password to protect the vault.

        Raises:
            VaultError: If the vault already exists.
        """
        if self._load_meta() is not None:
            raise VaultError("Vault already exists. Use unlock() instead.")

        # Derive key from password
        self._params = KeyDerivationParams.generate()
        key = derive_key(password, self._params)
        self._fernet = create_fernet(key)

        # Generate and store verification token
        token = generate_verification_token(self._fernet)
        self._save_meta(self._params, token)

    def unlock(self, password: str) -> bool:
        """Unlock the vault with the master password.

        Args:
            password: The master password.

        Returns:
            True if unlock succeeded.

        Raises:
            VaultUnlockError: If the password is incorrect.
        """
        meta = self._load_meta()
        if meta is None:
            raise VaultError("Vault does not exist. Call create() first.")

        # Reconstruct key derivation params
        # hash_params dict already contains salt (as base64 string),
        # so use from_dict which handles the full reconstruction
        self._params = KeyDerivationParams.from_dict(meta["hash_params"])

        # Derive key and verify
        key = derive_key(password, self._params)
        self._fernet = create_fernet(key)

        if not verify_master_key(self._fernet, meta["verification_token"]):
            self._fernet = None
            raise VaultUnlockError("Incorrect password.")

        return True

    def lock(self) -> None:
        """Lock the vault, clearing the master key from memory."""
        self._fernet = None
        self._params = None

    def change_password(self, old_password: str, new_password: str) -> None:
        """Change the vault master password.

        Args:
            old_password: Current password.
            new_password: New password to set.
        """
        fernet = self._ensure_unlocked()

        # Re-derive with new password
        new_params = KeyDerivationParams.generate()
        new_key = derive_key(new_password, new_params)
        new_fernet = create_fernet(new_key)

        # Re-encrypt all account secrets
        accounts = self._get_all_encrypted()
        for acc_data in accounts:
            old_secret = decrypt(fernet, acc_data["secret_encrypted"])
            acc_data["secret_encrypted"] = encrypt(new_fernet, old_secret)

            if acc_data.get("github_token_encrypted"):
                old_token = decrypt(fernet, acc_data["github_token_encrypted"])
                acc_data["github_token_encrypted"] = encrypt(new_fernet, old_token)

        app_secrets = self._get_all_app_secrets_encrypted()
        for secret_data in app_secrets:
            old_value = decrypt(fernet, secret_data["value_encrypted"])
            secret_data["value_encrypted"] = encrypt(new_fernet, old_value)

        # Save with new key
        self._save_all_encrypted(accounts, new_fernet)
        self._save_all_app_secrets_encrypted(app_secrets)
        token = generate_verification_token(new_fernet)
        self._save_meta(new_params, token)

        self._fernet = new_fernet
        self._params = new_params

    def add_account(self, account: OTPAccount) -> str:
        """Add an account to the vault.

        Args:
            account: The OTPAccount to add (secret in plaintext).

        Returns:
            The account ID.
        """
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        encrypted_secret = encrypt(fernet, account.secret)
        encrypted_token = (
            encrypt(fernet, account.github_token) if account.github_token else None
        )

        with get_session(self._db_path) as session:
            model = OTPAccountModel(
                id=account.id,
                issuer=account.issuer,
                name=account.name,
                secret_encrypted=encrypted_secret,
                otp_type=account.otp_type.value,
                algorithm=account.algorithm.value,
                digits=account.digits,
                period=account.period,
                counter=account.counter,
                icon=account.icon,
                group=account.group,
                is_github=account.is_github,
                github_token_encrypted=encrypted_token,
                notes=account.notes,
            )
            session.add(model)
            session.commit()

        return account.id

    def get_account(self, account_id: str) -> Optional[OTPAccount]:
        """Get a single account by ID.

        Args:
            account_id: The account UUID.

        Returns:
            OTPAccount with decrypted secret, or None if not found.
        """
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        with get_session(self._db_path) as session:
            model = session.exec(
                select(OTPAccountModel).where(OTPAccountModel.id == account_id)
            ).first()
            if model is None:
                return None
            return self._decrypt_model(model, fernet)

    def get_all_accounts(self) -> list[OTPAccount]:
        """Get all accounts with decrypted secrets.

        Returns:
            List of all OTPAccount instances.
        """
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        with get_session(self._db_path) as session:
            models = session.exec(select(OTPAccountModel)).all()
            return [self._decrypt_model(m, fernet) for m in models]

    def update_account(self, account: OTPAccount) -> None:
        """Update an existing account.

        Args:
            account: The OTPAccount with updated fields.
        """
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        encrypted_secret = encrypt(fernet, account.secret)
        encrypted_token = (
            encrypt(fernet, account.github_token) if account.github_token else None
        )

        with get_session(self._db_path) as session:
            model = session.exec(
                select(OTPAccountModel).where(OTPAccountModel.id == account.id)
            ).first()
            if model is None:
                raise VaultError(f"Account not found: {account.id}")

            model.issuer = account.issuer
            model.name = account.name
            model.secret_encrypted = encrypted_secret
            model.otp_type = account.otp_type.value
            model.algorithm = account.algorithm.value
            model.digits = account.digits
            model.period = account.period
            model.counter = account.counter
            model.icon = account.icon
            model.group = account.group
            model.is_github = account.is_github
            model.github_token_encrypted = encrypted_token
            model.notes = account.notes
            session.commit()

    def delete_account(self, account_id: str) -> bool:
        """Delete an account by ID.

        Args:
            account_id: The account UUID.

        Returns:
            True if the account was deleted.
        """
        self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        with get_session(self._db_path) as session:
            model = session.exec(
                select(OTPAccountModel).where(OTPAccountModel.id == account_id)
            ).first()
            if model is None:
                return False
            session.delete(model)
            session.commit()
            return True

    def import_from_uri(self, uri: str) -> OTPAccount:
        """Import an account from an otpauth:// URI.

        Args:
            uri: The otpauth:// URI string.

        Returns:
            The imported OTPAccount.
        """
        account = parse_otpauth_uri(uri)
        self.add_account(account)
        return account

    def export_uri_list(self) -> list[str]:
        """Export all accounts as otpauth:// URIs.

        Returns:
            List of otpauth:// URI strings.
        """
        accounts = self.get_all_accounts()
        return [to_provisioning_uri(acc) for acc in accounts]

    def export_encrypted_backup(self, backup_password: str) -> bytes:
        """Export the vault as an encrypted backup.

        Args:
            backup_password: Password to encrypt the backup (separate from master).

        Returns:
            Encrypted backup data.
        """
        accounts = self.get_all_accounts()
        backup_data = []
        for acc in accounts:
            backup_data.append({
                "issuer": acc.issuer,
                "name": acc.name,
                "secret": acc.secret,
                "otp_type": acc.otp_type.value,
                "algorithm": acc.algorithm.value,
                "digits": acc.digits,
                "period": acc.period,
                "counter": acc.counter,
                "group": acc.group,
                "is_github": acc.is_github,
                "notes": acc.notes,
            })

        # Encrypt backup with a separate key
        params = KeyDerivationParams.generate()
        key = derive_key(backup_password, params)
        fernet = create_fernet(key)

        plaintext = json.dumps(backup_data).encode("utf-8")
        encrypted = fernet.encrypt(plaintext)

        # Prepend params for later decryption
        header = json.dumps(params.to_dict()).encode("utf-8")
        header_len = len(header).to_bytes(4, "big")
        return header_len + header + encrypted

    def import_encrypted_backup(self, data: bytes, backup_password: str) -> int:
        """Import accounts from an encrypted backup.

        Args:
            data: The encrypted backup data.
            backup_password: Password to decrypt the backup.

        Returns:
            Number of accounts imported.
        """
        # Parse header
        header_len = int.from_bytes(data[:4], "big")
        header = json.loads(data[4 : 4 + header_len])
        encrypted = data[4 + header_len :]

        params = KeyDerivationParams.from_dict(header)
        key = derive_key(backup_password, params)
        fernet = create_fernet(key)

        plaintext = fernet.decrypt(encrypted).decode("utf-8")
        backup_data = json.loads(plaintext)

        count = 0
        for item in backup_data:
            account = OTPAccount(
                id=str(uuid.uuid4()),
                issuer=item["issuer"],
                name=item["name"],
                secret=item["secret"],
                otp_type=OTPType(item["otp_type"]),
                algorithm=Algorithm(item["algorithm"]),
                digits=item.get("digits", 6),
                period=item.get("period", 30),
                counter=item.get("counter", 0),
                group=item.get("group", "Default"),
                is_github=item.get("is_github", False),
                notes=item.get("notes"),
            )
            self.add_account(account)
            count += 1

        return count

    def save_github_connection(self, login: str, token: str) -> None:
        """Persist the GitHub OAuth connection token encrypted in the vault."""
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import AppSecretModel

        payload = json.dumps({"login": login, "token": token})
        encrypted = encrypt(fernet, payload)

        with get_session(self._db_path) as session:
            model = session.get(AppSecretModel, "github_connection")
            if model is None:
                model = AppSecretModel(
                    key="github_connection",
                    value_encrypted=encrypted,
                )
                session.add(model)
            else:
                model.value_encrypted = encrypted
                model.updated_at = datetime.now(timezone.utc)
            session.commit()

    def get_github_connection(self) -> Optional[dict[str, str]]:
        """Return the decrypted GitHub connection, if one is stored."""
        fernet = self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import AppSecretModel

        with get_session(self._db_path) as session:
            model = session.get(AppSecretModel, "github_connection")
            if model is None:
                return None
            return json.loads(decrypt(fernet, model.value_encrypted))

    def clear_github_connection(self) -> None:
        """Remove any persisted GitHub OAuth connection."""
        self._ensure_unlocked()

        from src.storage.database import get_session
        from src.storage.models import AppSecretModel

        with get_session(self._db_path) as session:
            model = session.get(AppSecretModel, "github_connection")
            if model is not None:
                session.delete(model)
                session.commit()

    @staticmethod
    def _decrypt_model(model, fernet: Fernet) -> OTPAccount:
        """Decrypt a database model into an OTPAccount."""
        secret = decrypt(fernet, model.secret_encrypted)
        github_token = None
        if model.github_token_encrypted:
            github_token = decrypt(fernet, model.github_token_encrypted)

        return OTPAccount(
            id=model.id,
            issuer=model.issuer,
            name=model.name,
            secret=secret,
            otp_type=OTPType(model.otp_type),
            algorithm=Algorithm(model.algorithm),
            digits=model.digits,
            period=model.period,
            counter=model.counter,
            icon=model.icon,
            group=model.group,
            is_github=model.is_github,
            github_token=github_token,
            notes=model.notes,
        )

    def _get_all_encrypted(self) -> list[dict]:
        """Get all accounts as raw encrypted dicts."""
        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        with get_session(self._db_path) as session:
            models = session.exec(select(OTPAccountModel)).all()
            return [
                {
                    "id": m.id,
                    "secret_encrypted": m.secret_encrypted,
                    "github_token_encrypted": m.github_token_encrypted,
                }
                for m in models
            ]

    def _save_all_encrypted(self, accounts: list[dict], fernet: Fernet) -> None:
        """Save re-encrypted account data."""
        from src.storage.database import get_session
        from src.storage.models import OTPAccountModel

        with get_session(self._db_path) as session:
            for acc in accounts:
                model = session.exec(
                    select(OTPAccountModel).where(OTPAccountModel.id == acc["id"])
                ).first()
                if model:
                    model.secret_encrypted = acc["secret_encrypted"]
                    model.github_token_encrypted = acc["github_token_encrypted"]
            session.commit()

    def _get_all_app_secrets_encrypted(self) -> list[dict]:
        """Get app secrets as raw encrypted dicts."""
        from src.storage.database import get_session
        from src.storage.models import AppSecretModel

        with get_session(self._db_path) as session:
            models = session.exec(select(AppSecretModel)).all()
            return [
                {
                    "key": m.key,
                    "value_encrypted": m.value_encrypted,
                }
                for m in models
            ]

    def _save_all_app_secrets_encrypted(self, app_secrets: list[dict]) -> None:
        """Save re-encrypted app secret data."""
        from src.storage.database import get_session
        from src.storage.models import AppSecretModel

        with get_session(self._db_path) as session:
            for item in app_secrets:
                model = session.get(AppSecretModel, item["key"])
                if model:
                    model.value_encrypted = item["value_encrypted"]
                    model.updated_at = datetime.now(timezone.utc)
            session.commit()
