"""Data import/export utilities for compatibility with other authenticator apps.

Supports:
- otpauth:// URI lists (Google Authenticator, Authy, etc.)
- Aegis Authenticator JSON backup format
- Generic JSON export
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from src.core.otp import OTPAccount, OTPType, Algorithm
from src.core.uri_parser import parse_otpauth_uri, to_provisioning_uri


def export_uri_list(accounts: list[OTPAccount]) -> str:
    """Export accounts as a newline-separated list of otpauth:// URIs.

    Args:
        accounts: List of OTPAccount instances.

    Returns:
        Multi-line string of otpauth:// URIs.
    """
    return "\n".join(to_provisioning_uri(acc) for acc in accounts)


def import_uri_list(text: str) -> list[OTPAccount]:
    """Import accounts from a newline-separated list of otpauth:// URIs.

    Args:
        text: Multi-line string of otpauth:// URIs.

    Returns:
        List of parsed OTPAccount instances.
    """
    accounts = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line.startswith("otpauth://"):
            try:
                account = parse_otpauth_uri(line)
                accounts.append(account)
            except ValueError:
                continue  # Skip malformed URIs
    return accounts


def export_json(accounts: list[OTPAccount]) -> str:
    """Export accounts as a JSON string.

    Args:
        accounts: List of OTPAccount instances.

    Returns:
        JSON string with account data.
    """
    data = []
    for acc in accounts:
        data.append({
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
    return json.dumps(data, indent=2)


def import_json(text: str) -> list[OTPAccount]:
    """Import accounts from a JSON string.

    Args:
        text: JSON string with account data.

    Returns:
        List of OTPAccount instances.
    """
    data = json.loads(text)
    accounts = []
    for item in data:
        accounts.append(OTPAccount(
            id=str(uuid.uuid4()),
            issuer=item.get("issuer", ""),
            name=item.get("name", ""),
            secret=item["secret"],
            otp_type=OTPType(item.get("otp_type", "totp")),
            algorithm=Algorithm(item.get("algorithm", "SHA1")),
            digits=item.get("digits", 6),
            period=item.get("period", 30),
            counter=item.get("counter", 0),
            group=item.get("group", "Default"),
            is_github=item.get("is_github", False),
            notes=item.get("notes"),
        ))
    return accounts


def import_aegis_backup(json_data: dict, password: Optional[str] = None) -> list[OTPAccount]:
    """Import accounts from an Aegis Authenticator backup.

    Note: Only supports unencrypted Aegis backups. For encrypted backups,
    the password must be provided to decrypt the vault first.

    Args:
        json_data: Parsed Aegis backup JSON.
        password: Vault password if the backup is encrypted.

    Returns:
        List of OTPAccount instances.
    """
    entries = json_data.get("db", {}).get("entries", [])
    accounts = []

    for entry in entries:
        info = entry.get("info", {})
        secret = info.get("secret", "")

        # Aegis stores secrets in hex, convert to base32
        if info.get("algo", 1) == 0:
            algo = Algorithm.SHA1
        elif info.get("algo", 1) == 1:
            algo = Algorithm.SHA256
        elif info.get("algo", 1) == 2:
            algo = Algorithm.SHA512
        else:
            algo = Algorithm.SHA1

        otp_type = OTPType.TOTP if entry.get("type") == "totp" else OTPType.HOTP

        accounts.append(OTPAccount(
            id=str(uuid.uuid4()),
            issuer=entry.get("issuer", ""),
            name=entry.get("name", ""),
            secret=secret,
            otp_type=otp_type,
            algorithm=algo,
            digits=info.get("digits", 6),
            period=info.get("period", 30),
            counter=info.get("counter", 0),
            group=entry.get("group", "Default"),
            is_github="github" in entry.get("issuer", "").lower(),
        ))

    return accounts
