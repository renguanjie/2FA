"""otpauth:// URI parsing and generation.

Implements the Key URI Format specification used by Google Authenticator
and other TOTP/HOTP apps.

Format: otpauth://TYPE/LABEL?PARAMETERS
  - TYPE: "totp" or "hotp"
  - LABEL: "issuer:account" or just "account"
  - PARAMETERS: secret, issuer, algorithm, digits, period, counter

Reference: https://github.com/google/google-authenticator/wiki/Key-Uri-Format
"""

from __future__ import annotations

import re
import uuid
from urllib.parse import parse_qs, quote, unquote, urlparse

from src.core.otp import OTPAccount, OTPType, Algorithm


# Pattern to parse label: "Issuer:AccountName" or just "AccountName"
_LABEL_PATTERN = re.compile(r"^(?:(.+?):)?(.+)$")


def parse_otpauth_uri(uri: str) -> OTPAccount:
    """Parse an otpauth:// URI into an OTPAccount.

    Args:
        uri: The otpauth:// URI string.

    Returns:
        Parsed OTPAccount instance.

    Raises:
        ValueError: If the URI is malformed or missing required fields.
    """
    if not uri.startswith("otpauth://"):
        raise ValueError(f"Invalid URI scheme, expected otpauth://, got: {uri[:20]}")

    parsed = urlparse(uri)

    # Parse type (totp or hotp)
    otp_type_str = parsed.hostname  # "totp" or "hotp"
    if otp_type_str not in ("totp", "hotp"):
        raise ValueError(f"Invalid OTP type: {otp_type_str}")
    otp_type = OTPType(otp_type_str)

    # Parse label: "/Issuer:Account" or "/Account"
    label = unquote(parsed.path.lstrip("/"))
    match = _LABEL_PATTERN.match(label)
    if not match:
        raise ValueError(f"Invalid label: {label}")

    issuer_from_label = match.group(1)  # May be None
    account_name = match.group(2)

    # Parse query parameters
    params = parse_qs(parsed.query)

    # Required: secret
    secret = params.get("secret", [None])[0]
    if not secret:
        raise ValueError("Missing required parameter: secret")

    # Optional parameters
    issuer = params.get("issuer", [issuer_from_label])[0] or ""
    algorithm_str = params.get("algorithm", ["SHA1"])[0].upper()
    digits = int(params.get("digits", ["6"])[0])
    period = int(params.get("period", ["30"])[0])
    counter = int(params.get("counter", ["0"])[0])

    # Validate algorithm
    try:
        algorithm = Algorithm(algorithm_str)
    except ValueError:
        raise ValueError(f"Unsupported algorithm: {algorithm_str}")

    # Detect GitHub accounts
    is_github = issuer.lower() in ("github", "github.com") or "github" in account_name.lower()

    return OTPAccount(
        id=str(uuid.uuid4()),
        issuer=issuer,
        name=account_name,
        secret=secret.upper(),  # Normalize to uppercase Base32
        otp_type=otp_type,
        algorithm=algorithm,
        digits=digits,
        period=period,
        counter=counter,
        is_github=is_github,
    )


def to_provisioning_uri(
    account: OTPAccount,
    include_issuer_in_label: bool = True,
) -> str:
    """Generate an otpauth:// provisioning URI from an OTPAccount.

    Args:
        account: The OTPAccount to convert.
        include_issuer_in_label: Whether to include issuer in the label path.

    Returns:
        otpauth:// URI string compatible with authenticator apps.
    """
    # Build label
    if include_issuer_in_label and account.issuer:
        label = f"{quote(account.issuer)}:{quote(account.name)}"
    else:
        label = quote(account.name)

    # Build query parameters
    params = {
        "secret": account.secret,
        "issuer": account.issuer,
        "algorithm": account.algorithm.value,
        "digits": str(account.digits),
    }

    if account.otp_type == OTPType.TOTP:
        params["period"] = str(account.period)
    else:
        params["counter"] = str(account.counter)

    query = "&".join(f"{k}={quote(v)}" for k, v in params.items())

    return f"otpauth://{account.otp_type.value}/{label}?{query}"
