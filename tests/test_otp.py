"""Tests for OTP generation and verification."""


from src.core.otp import OTPService, OTPAccount, OTPType, Algorithm


class TestTOTP:
    """Test TOTP generation and verification."""

    def test_generate_secret(self):
        secret = OTPService.generate_secret()
        assert len(secret) >= 32
        assert secret.isalnum() or all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=" for c in secret)

    def test_generate_totp(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_totp(secret)
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_totp(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_totp(secret)
        assert OTPService.verify_totp(secret, code) is True

    def test_verify_totp_wrong_code(self):
        secret = "JBSWY3DPEHPK3PXP"
        assert OTPService.verify_totp(secret, "000000") is False

    def test_totp_with_sha256(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_totp(secret, algorithm="SHA256")
        assert len(code) == 6
        assert OTPService.verify_totp(secret, code, algorithm="SHA256") is True

    def test_totp_with_sha512(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_totp(secret, algorithm="SHA512")
        assert len(code) == 6
        assert OTPService.verify_totp(secret, code, algorithm="SHA512") is True

    def test_totp_custom_digits(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_totp(secret, digits=8)
        assert len(code) == 8
        assert OTPService.verify_totp(secret, code, digits=8) is True

    def test_totp_remaining_seconds(self):
        remaining = OTPService.get_remaining_seconds(period=30)
        assert 0 <= remaining < 30

    def test_totp_github_params(self):
        """Test with GitHub's standard TOTP parameters."""
        secret = "JBSWY3DPEHPK3PXP"
        # GitHub uses SHA1, 6 digits, 30s period
        code = OTPService.generate_totp(secret, algorithm="SHA1", digits=6, period=30)
        assert len(code) == 6
        assert OTPService.verify_totp(secret, code, algorithm="SHA1", digits=6, period=30) is True


class TestHOTP:
    """Test HOTP generation and verification."""

    def test_generate_hotp(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_hotp(secret, counter=0)
        assert len(code) == 6
        assert code.isdigit()

    def test_hotp_counter_increments(self):
        secret = "JBSWY3DPEHPK3PXP"
        code0 = OTPService.generate_hotp(secret, counter=0)
        code1 = OTPService.generate_hotp(secret, counter=1)
        assert code0 != code1

    def test_verify_hotp(self):
        secret = "JBSWY3DPEHPK3PXP"
        code = OTPService.generate_hotp(secret, counter=5)
        assert OTPService.verify_hotp(secret, code, counter=5) is True


class TestOTPAccount:
    """Test OTPAccount model."""

    def test_create_account(self):
        account = OTPAccount(
            id="test-1",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )
        assert account.issuer == "GitHub"
        assert account.otp_type == OTPType.TOTP
        assert account.algorithm == Algorithm.SHA1
        assert account.is_github is False

    def test_github_account(self):
        account = OTPAccount(
            id="test-2",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
            is_github=True,
        )
        assert account.is_github is True

    def test_generate_for_account(self):
        account = OTPAccount(
            id="test-3",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )
        code = OTPService.generate_for_account(account)
        assert len(code) == 6

    def test_to_dict_excludes_secret(self):
        account = OTPAccount(
            id="test-4",
            issuer="GitHub",
            name="user@example.com",
            secret="JBSWY3DPEHPK3PXP",
        )
        d = account.to_dict()
        assert "secret" not in d
        assert d["issuer"] == "GitHub"
