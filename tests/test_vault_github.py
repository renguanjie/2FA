"""Tests for encrypted GitHub connection token storage."""

from src.core.vault import Vault


def test_github_connection_token_roundtrip(tmp_path):
    vault = Vault(tmp_path / "vault.db")
    vault.create("password123")

    vault.save_github_connection("octocat", "gho_secret")
    vault.lock()
    vault.unlock("password123")

    connection = vault.get_github_connection()

    assert connection == {"login": "octocat", "token": "gho_secret"}


def test_github_connection_can_be_cleared(tmp_path):
    vault = Vault(tmp_path / "vault.db")
    vault.create("password123")
    vault.save_github_connection("octocat", "gho_secret")

    vault.clear_github_connection()

    assert vault.get_github_connection() is None
