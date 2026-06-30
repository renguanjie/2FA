"""Tests for otpauth:// URI parsing and generation."""

import pytest

from src.core.otp import OTPAccount, OTPType, Algorithm
from src.core.uri_parser import parse_otpauth_uri, to_provisioning_uri


class TestParseURI:
    """Test otpauth:// URI parsing."""

    def test_parse_basic_totp(self):
        uri = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub"
        account = parse_otpauth_uri(uri)

        assert account.issuer == "GitHub"
        assert account.name == "user@example.com"
        assert account.secret == "JBSWY3DPEHPK3PXP"
        assert account.otp_type == OTPType.TOTP
        assert account.algorithm == Algorithm.SHA1
        assert account.digits == 6
        assert account.period == 30
        assert account.is_github is True

    def test_parse_hotp(self):
        uri = "otpauth://hotp/Service:user@example.com?secret=JBSWY3DPEHPK3PXP&counter=5"
        account = parse_otpauth_uri(uri)

        assert account.otp_type == OTPType.HOTP
        assert account.counter == 5

    def test_parse_with_algorithm(self):
        uri = "otpauth://totp/Service:user@example.com?secret=JBSWY3DPEHPK3PXP&algorithm=SHA256"
        account = parse_otpauth_uri(uri)
        assert account.algorithm == Algorithm.SHA256

    def test_parse_with_digits(self):
        uri = "otpauth://totp/Service:user@example.com?secret=JBSWY3DPEHPK3PXP&digits=8"
        account = parse_otpauth_uri(uri)
        assert account.digits == 8

    def test_parse_with_period(self):
        uri = "otpauth://totp/Service:user@example.com?secret=JBSWY3DPEHPK3PXP&period=60"
        account = parse_otpauth_uri(uri)
        assert account.period == 60

    def test_parse_label_without_issuer(self):
        uri = "otpauth://totp/user@example.com?secret=JBSWY3DPEHPK3PXP"
        account = parse_otpauth_uri(uri)
        assert account.name == "user@example.com"

    def test_parse_github_detected(self):
        uri = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub"
        account = parse_otpauth_uri(uri)
        assert account.is_github is True

    def test_parse_invalid_scheme(self):
        with pytest.raises(ValueError, match="Invalid URI scheme"):
            parse_otpauth_uri("https://example.com")

    def test_parse_missing_secret(self):
        uri = "otpauth://totp/Service:user@example.com"
        with pytest.raises(ValueError, match="Missing required parameter"):
            parse_otpauth_uri(uri)

    def test_parse_invalid_type(self):
        uri = "otpauth://invalid/user?secret=JBSWY3DPEHPK3PXP"
        with pytest.raises(ValueError, match="Invalid OTP type"):
            parse_otpauth_uri(uri)


class TestGenerateURI:
    """Test otpauth:// URI generation."""

    def test_generate_basic(self):
        account = OTPAccount(
            id="test",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )
        uri = to_provisioning_uri(account)

        assert uri.startswith("otpauth://totp/")
        assert "GitHub" in uri
        assert "JBSWY3DPEHPK3PXP" in uri
        assert "issuer=GitHub" in uri

    def test_roundtrip(self):
        """Parse then generate should produce equivalent URI."""
        original = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub&algorithm=SHA1&digits=6&period=30"
        account = parse_otpauth_uri(original)
        generated = to_provisioning_uri(account)

        # Parse both to compare
        a1 = parse_otpauth_uri(original)
        a2 = parse_otpauth_uri(generated)

        assert a1.issuer == a2.issuer
        assert a1.name == a2.name
        assert a1.secret == a2.secret
        assert a1.otp_type == a2.otp_type
        assert a1.algorithm == a2.algorithm
        assert a1.digits == a2.digits
        assert a1.period == a2.period

    def test_generate_hotp(self):
        account = OTPAccount(
            id="test",
            issuer="Service",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
            otp_type=OTPType.HOTP,
            counter=5,
        )
        uri = to_provisioning_uri(account)
        assert "otpauth://hotp/" in uri
        assert "counter=5" in uri
