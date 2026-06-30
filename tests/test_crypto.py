"""Tests for cryptographic operations."""

import pytest

from src.core.crypto import (
    KeyDerivationParams,
    create_fernet,
    decrypt,
    derive_key,
    encrypt,
    generate_verification_token,
    verify_master_key,
)


class TestKeyDerivation:
    """Test Argon2id key derivation."""

    def test_derive_key(self):
        params = KeyDerivationParams.generate()
        key = derive_key("test_password", params)
        assert len(key) > 0

    def test_same_password_same_key(self):
        params = KeyDerivationParams(salt=b"fixed_salt_12345")
        key1 = derive_key("test_password", params)
        key2 = derive_key("test_password", params)
        assert key1 == key2

    def test_different_password_different_key(self):
        params = KeyDerivationParams.generate()
        key1 = derive_key("password1", params)
        key2 = derive_key("password2", params)
        assert key1 != key2

    def test_different_salt_different_key(self):
        params1 = KeyDerivationParams(salt=b"salt_one_123456")
        params2 = KeyDerivationParams(salt=b"salt_two_123456")
        key1 = derive_key("same_password", params1)
        key2 = derive_key("same_password", params2)
        assert key1 != key2


class TestFernetEncryption:
    """Test Fernet symmetric encryption."""

    def test_encrypt_decrypt(self):
        params = KeyDerivationParams.generate()
        key = derive_key("test_password", params)
        fernet = create_fernet(key)

        plaintext = "my_secret_totp_key"
        ciphertext = encrypt(fernet, plaintext)
        decrypted = decrypt(fernet, ciphertext)

        assert decrypted == plaintext

    def test_encrypt_different_each_time(self):
        params = KeyDerivationParams.generate()
        key = derive_key("test_password", params)
        fernet = create_fernet(key)

        c1 = encrypt(fernet, "same_text")
        c2 = encrypt(fernet, "same_text")
        assert c1 != c2  # Fernet includes random IV

    def test_wrong_key_fails(self):
        params1 = KeyDerivationParams.generate()
        params2 = KeyDerivationParams.generate()
        key1 = derive_key("password1", params1)
        key2 = derive_key("password2", params2)

        fernet1 = create_fernet(key1)
        fernet2 = create_fernet(key2)

        ciphertext = encrypt(fernet1, "secret")
        with pytest.raises(Exception):
            decrypt(fernet2, ciphertext)


class TestVerification:
    """Test master key verification."""

    def test_generate_and_verify(self):
        params = KeyDerivationParams.generate()
        key = derive_key("test_password", params)
        fernet = create_fernet(key)

        token = generate_verification_token(fernet)
        assert verify_master_key(fernet, token) is True

    def test_wrong_key_verify_fails(self):
        params = KeyDerivationParams.generate()
        key1 = derive_key("correct_password", params)
        key2 = derive_key("wrong_password", params)

        fernet1 = create_fernet(key1)
        fernet2 = create_fernet(key2)

        token = generate_verification_token(fernet1)
        assert verify_master_key(fernet2, token) is False


class TestKeyDerivationParams:
    """Test KeyDerivationParams serialization."""

    def test_to_dict_and_back(self):
        params = KeyDerivationParams.generate()
        d = params.to_dict()

        restored = KeyDerivationParams.from_dict(d)
        assert restored.salt == params.salt
        assert restored.time_cost == params.time_cost
        assert restored.memory_cost == params.memory_cost
        assert restored.parallelism == params.parallelism
