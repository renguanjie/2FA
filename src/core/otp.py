"""TOTP/HOTP generation and verification.

Implements RFC 6238 (TOTP) and RFC 4226 (HOTP) using pyotp.
Reference: https://github.com/pyauth/pyotp
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pyotp


class OTPType(str, Enum):
    TOTP = "totp"
    HOTP = "hotp"


class Algorithm(str, Enum):
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    SHA512 = "SHA512"


@dataclass
class OTPAccount:
    """Represents a single OTP account entry."""

    id: str                          # UUID
    issuer: str                      # e.g. "GitHub"
    name: str                        # e.g. "user@email.com"
    secret: str                      # Base32-encoded secret (plaintext, only in memory)
    otp_type: OTPType = OTPType.TOTP
    algorithm: Algorithm = Algorithm.SHA1
    digits: int = 6
    period: int = 30                 # TOTP interval in seconds
    counter: int = 0                 # HOTP counter
    icon: Optional[str] = None
    group: str = "Default"
    is_github: bool = False
    github_token: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dict (secrets excluded)."""
        return {
            "id": self.id,
            "issuer": self.issuer,
            "name": self.name,
            "otp_type": self.otp_type.value,
            "algorithm": self.algorithm.value,
            "digits": self.digits,
            "period": self.period,
            "counter": self.counter,
            "icon": self.icon,
            "group": self.group,
            "is_github": self.is_github,
            "notes": self.notes,
        }


class OTPService:
    """OTP generation and verification service.

    Wraps pyotp to provide a clean interface for TOTP and HOTP operations.
    GitHub uses standard TOTP with SHA1, 6 digits, 30-second period.
    """

    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate a random Base32-encoded secret key.

        Args:
            length: Byte length of the random secret (default 32 = 256 bits).

        Returns:
            Base32-encoded secret string.
        """
        return pyotp.random_base32(length)

    @staticmethod
    def _build_totp(
        secret: str,
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
    ) -> pyotp.TOTP:
        """Build a pyotp.TOTP instance with the given parameters."""
        return pyotp.TOTP(
            secret,
            digits=digits,
            digest=algorithm.lower().replace("sha", "sha"),
            interval=period,
        )

    @staticmethod
    def _build_hotp(
        secret: str,
        algorithm: str = "SHA1",
        digits: int = 6,
    ) -> pyotp.HOTP:
        """Build a pyotp.HOTP instance with the given parameters."""
        return pyotp.HOTP(
            secret,
            digits=digits,
            digest=algorithm.lower().replace("sha", "sha"),
        )

    @classmethod
    def generate_totp(
        cls,
        secret: str,
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
    ) -> str:
        """Generate the current TOTP code.

        Args:
            secret: Base32-encoded secret key.
            algorithm: Hash algorithm (SHA1/SHA256/SHA512).
            digits: Number of digits in the code.
            period: Time step in seconds.

        Returns:
            Current OTP code string (e.g. "492039").
        """
        totp = cls._build_totp(secret, algorithm, digits, period)
        return totp.now()

    @classmethod
    def verify_totp(
        cls,
        secret: str,
        code: str,
        algorithm: str = "SHA1",
        digits: int = 6,
        period: int = 30,
        window: int = 1,
    ) -> bool:
        """Verify a TOTP code.

        Args:
            secret: Base32-encoded secret key.
            code: The code to verify.
            algorithm: Hash algorithm.
            digits: Number of digits.
            period: Time step in seconds.
            window: Number of time steps to check before/after current.

        Returns:
            True if the code is valid.
        """
        totp = cls._build_totp(secret, algorithm, digits, period)
        return totp.verify(code, valid_window=window)

    @classmethod
    def generate_hotp(
        cls,
        secret: str,
        counter: int,
        algorithm: str = "SHA1",
        digits: int = 6,
    ) -> str:
        """Generate an HOTP code for the given counter value."""
        hotp = cls._build_hotp(secret, algorithm, digits)
        return hotp.at(counter)

    @classmethod
    def verify_hotp(
        cls,
        secret: str,
        code: str,
        counter: int,
        algorithm: str = "SHA1",
        digits: int = 6,
        window: int = 10,
    ) -> bool:
        """Verify an HOTP code.

        Checks the code against counter and counter+1..counter+window
        to allow for slight counter drift.
        """
        hotp = cls._build_hotp(secret, algorithm, digits)
        # pyotp HOTP.verify doesn't support valid_window, so check manually
        for i in range(counter, counter + window + 1):
            if hotp.verify(code, i):
                return True
        return False

    @staticmethod
    def get_remaining_seconds(period: int = 30) -> int:
        """Get the number of seconds remaining in the current TOTP period.

        Args:
            period: Time step in seconds.

        Returns:
            Seconds remaining (0 to period-1).
        """
        import time
        return period - int(time.time()) % period

    @classmethod
    def generate_for_account(cls, account: OTPAccount) -> str:
        """Generate the current OTP code for an account.

        Args:
            account: The OTPAccount to generate a code for.

        Returns:
            Current OTP code string.
        """
        if account.otp_type == OTPType.TOTP:
            return cls.generate_totp(
                account.secret,
                account.algorithm.value,
                account.digits,
                account.period,
            )
        else:
            return cls.generate_hotp(
                account.secret,
                account.counter,
                account.algorithm.value,
                account.digits,
            )

    @classmethod
    def verify_for_account(cls, account: OTPAccount, code: str) -> bool:
        """Verify an OTP code against an account.

        Args:
            account: The OTPAccount to verify against.
            code: The code to verify.

        Returns:
            True if the code is valid.
        """
        if account.otp_type == OTPType.TOTP:
            return cls.verify_totp(
                account.secret,
                code,
                account.algorithm.value,
                account.digits,
                account.period,
            )
        else:
            return cls.verify_hotp(
                account.secret,
                code,
                account.counter,
                account.algorithm.value,
                account.digits,
            )
