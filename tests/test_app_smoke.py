"""Headless UI smoke tests.

These do not open a real Flet window (impossible in CI/headless). Instead they
drive the app shell and every page with a stub Page object, verifying that all
UI is constructed without raising — this is what catches breakage from Flet API
changes such as the ElevatedButton -> Button migration.
"""

import flet as ft
import pytest

from src.config import Config
from src.ui.app import TwoFAApp


class FakeWindow:
    width = 0
    height = 0


class FakePage:
    """Minimal stand-in for flet.Page used during construction."""

    def __init__(self):
        self.title = ""
        self.theme = None
        self.theme_mode = None
        self.padding = None
        self.window = FakeWindow()
        self.on_keyboard_event = None
        self.controls: list = []
        self.overlay: list = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        pass

    def show_snack_bar(self, snack):
        pass


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Construct TwoFAApp against a temp DB and a fake page."""
    db_path = tmp_path / "vault.db"
    monkeypatch.setattr(Config, "get_db_path", staticmethod(lambda: db_path))

    page = FakePage()
    application = TwoFAApp(page)
    return application, page, db_path


def test_app_constructs_and_shows_lock(app):
    application, page, _ = app
    # The shell built its nav bar, FAB, and lock screen without raising.
    assert application._nav_bar is not None
    assert application._fab is not None
    # Lock screen is the first content shown.
    assert page.controls, "lock screen should have been added to the page"


def test_every_page_builds_after_unlock(app):
    application, _, db_path = app

    # Create and unlock a real vault so pages that read accounts work.
    vault = application._vault
    vault.create("password123")
    vault.unlock("password123")
    assert vault.is_unlocked

    # Drive construction of each page directly (avoids the asyncio auto-lock
    # task that _on_vault_unlocked would start outside an event loop).
    application._show_home()
    assert application._home_page is not None

    application._show_github()
    assert application._github_page is not None

    application._show_settings()
    assert application._settings_page is not None

    application._show_backup()
    assert application._backup_page is not None

    application._show_add_page()
    assert application._add_page is not None


def test_nav_change_routes_to_each_tab(app):
    application, _, _ = app
    application._vault.create("password123")
    application._vault.unlock("password123")

    class Evt:
        def __init__(self, idx):
            self.control = type("C", (), {"selected_index": idx})()

    application._on_nav_change(Evt(1))
    assert application._current_index == 1
    application._on_nav_change(Evt(2))
    assert application._current_index == 2
    application._on_nav_change(Evt(0))
    assert application._current_index == 0


def test_flet_button_helper_uses_current_api():
    """The compat button() should resolve to ft.Button on modern Flet."""
    from src.ui.flet_compat import button

    btn = button("Click")
    # On Flet >= 0.80 this is ft.Button; older falls back to ElevatedButton.
    assert isinstance(btn, (getattr(ft, "Button", ()), ft.ElevatedButton))
