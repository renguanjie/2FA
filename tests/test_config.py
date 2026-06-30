"""Tests for persisted application settings."""

from src.config import Config


def test_settings_roundtrip_persists_values(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "get_data_dir", staticmethod(lambda: tmp_path))

    Config.GITHUB_CLIENT_ID = ""
    Config.GITHUB_CLIENT_SECRET = ""
    Config.AUTO_LOCK_SECONDS = 300
    Config.CLIPBOARD_CLEAR_SECONDS = 30

    Config.save_settings(
        github_client_id="client-123",
        github_client_secret="secret-456",
        auto_lock_seconds=60,
        clipboard_clear_seconds=10,
    )

    Config.GITHUB_CLIENT_ID = ""
    Config.GITHUB_CLIENT_SECRET = ""
    Config.AUTO_LOCK_SECONDS = 300
    Config.CLIPBOARD_CLEAR_SECONDS = 30

    Config.load_settings()

    assert Config.GITHUB_CLIENT_ID == "client-123"
    assert Config.GITHUB_CLIENT_SECRET == "secret-456"
    assert Config.AUTO_LOCK_SECONDS == 60
    assert Config.CLIPBOARD_CLEAR_SECONDS == 10
