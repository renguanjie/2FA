"""Cryptographic operations for the 2FA vault.

Uses Argon2id for key derivation and Fernet (AES-128-CBC + HMAC-SHA256)
for symmetric encryption. Reference: Aegis Authenticator's vault design.

Security parameters:
  - Argon2id: memory=64MB, iterations=3, parallelism=4
  - Fernet: AES-128-CBC with PKCS7 padding + HMAC-SHA256
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.fernet import Fernet, InvalidToken


@dataclass
class KeyDerivationParams:
    """Parameters for Argon2id key derivation."""

    salt: bytes
    time_cost: int = 3
    memory_cost: int = 65536  # 64 MB in KB
    parallelism: int = 4
    hash_len: int = 32        # 256-bit key

    def to_dict(self) -> dict:
        return {
            "salt": base64.b64encode(self.salt).decode(),
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.parallelism,
            "hash_len": self.hash_len,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyDerivationParams:
        return cls(
            salt=base64.b64decode(data["salt"]),
            time_cost=data["time_cost"],
            memory_cost=data["memory_cost"],
            parallelism=data["parallelism"],
            hash_len=data["hash_len"],
        )

    @classmethod
    def generate(cls, **kwargs) -> KeyDerivationParams:
        """Generate new params with a random salt."""
        salt = kwargs.pop("salt", None) or os.urandom(16)
        return cls(salt=salt, **kwargs)


def derive_key(password: str, params: KeyDerivationParams) -> bytes:
    """Derive a 256-bit key from a password using Argon2id.

    Args:
        password: User-provided password.
        params: Key derivation parameters (salt, iterations, memory, parallelism).

    Returns:
        32-byte derived key suitable for Fernet.
    """
    raw_key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=params.salt,
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        hash_len=params.hash_len,
        type=Type.ID,
    )
    # Fernet requires a 32-byte base64-url-encoded key
    return base64.urlsafe_b64encode(raw_key)


def create_fernet(key: bytes) -> Fernet:
    """Create a Fernet instance from a derived key."""
    return Fernet(key)


def encrypt(fernet: Fernet, plaintext: str) -> bytes:
    """Encrypt a string using Fernet.

    Args:
        fernet: Fernet instance with the derived key.
        plaintext: String to encrypt.

    Returns:
        Encrypted bytes (includes timestamp, IV, ciphertext, HMAC).
    """
    return fernet.encrypt(plaintext.encode("utf-8"))


def decrypt(fernet: Fernet, ciphertext: bytes) -> str:
    """Decrypt Fernet-encrypted bytes back to a string.

    Args:
        fernet: Fernet instance with the derived key.
        ciphertext: Encrypted bytes.

    Returns:
        Decrypted string.

    Raises:
        InvalidToken: If the key is wrong or data is tampered.
    """
    return fernet.decrypt(ciphertext).decode("utf-8")


def encrypt_bytes(fernet: Fernet, data: bytes) -> bytes:
    """Encrypt raw bytes using Fernet."""
    return fernet.encrypt(data)


def decrypt_bytes(fernet: Fernet, data: bytes) -> bytes:
    """Decrypt raw bytes using Fernet."""
    return fernet.decrypt(data)


def generate_verification_token(fernet: Fernet) -> bytes:
    """Generate and encrypt a verification token to validate the master password.

    The token is a known plaintext encrypted with the master key.
    On unlock, we decrypt and verify this token to confirm the password is correct.
    """
    known_plaintext = "two-fa-vault-verify-v1"
    return encrypt(fernet, known_plaintext)


def verify_master_key(fernet: Fernet, token: bytes) -> bool:
    """Verify that a Fernet instance was created with the correct master key.

    Args:
        fernet: Fernet instance to verify.
        token: The verification token stored during vault creation.

    Returns:
        True if the key is correct.
    """
    try:
        plaintext = decrypt(fernet, token)
        return plaintext == "two-fa-vault-verify-v1"
    except (InvalidToken, Exception):
        return False
