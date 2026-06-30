"""Tests for lock screen behavior."""

import pytest

from src.config import Config
from src.core.vault import VaultUnlockError
from src.ui.pages.lock import LockPage


class FakePage:
    def show_snack_bar(self, snack):
        pass


class FakeVault:
    def __init__(self):
        self.unlock_calls = 0

    def _load_meta(self):
        return {"exists": True}

    def unlock(self, password):
        self.unlock_calls += 1
        if self.unlock_calls <= Config.MAX_UNLOCK_ATTEMPTS:
            raise VaultUnlockError("bad password")
        return True


@pytest.mark.asyncio
async def test_unlock_attempts_are_allowed_again_after_delay(monkeypatch):
    monkeypatch.setattr(Config, "MAX_UNLOCK_ATTEMPTS", 2)
    monkeypatch.setattr(Config, "UNLOCK_DELAY_SECONDS", 30)

    now = [1000.0]
    monkeypatch.setattr("src.ui.pages.lock.time.monotonic", lambda: now[0])

    vault = FakeVault()
    page = LockPage(vault=vault, page=FakePage())
    page.update = lambda: None
    page._is_creating = False
    page._password_field.value = "wrong"

    await page._on_submit(None)
    await page._on_submit(None)
    await page._on_submit(None)
    assert vault.unlock_calls == 2

    now[0] += 31
    await page._on_submit(None)

    assert vault.unlock_calls == 3
