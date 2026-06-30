"""Tests for console entry point behavior."""

import flet as ft

from src import main as main_module
from src.config import Config


def test_main_without_page_starts_flet(monkeypatch):
    """main() with no page launches Flet with app_main as the target.

    The entry point prefers ft.run (Flet >= 0.80) and falls back to ft.app.
    Both are stubbed so no real window/server is started.
    """
    calls = {}

    def fake_run(target, *args, **kwargs):
        calls["launcher"] = "run"
        calls["target"] = target

    def fake_app(target, *args, **kwargs):
        calls["launcher"] = "app"
        calls["target"] = target

    monkeypatch.setattr(main_module.ft, "app", fake_app)
    if hasattr(ft, "run"):
        monkeypatch.setattr(main_module.ft, "run", fake_run)

    main_module.main()

    assert calls["target"] is main_module.app_main
    # On modern Flet the preferred launcher is run(); older uses app().
    assert calls["launcher"] == ("run" if hasattr(ft, "run") else "app")


def test_main_with_page_builds_app_inline(monkeypatch, tmp_path):
    """main(page) wires the app onto the provided page without launching Flet."""
    monkeypatch.setattr(Config, "get_db_path", staticmethod(lambda: tmp_path / "vault.db"))
    launched = {"called": False}
    monkeypatch.setattr(main_module.ft, "app", lambda *a, **k: launched.__setitem__("called", True))
    if hasattr(ft, "run"):
        monkeypatch.setattr(main_module.ft, "run", lambda *a, **k: launched.__setitem__("called", True))

    class FakeWindow:
        width = 0
        height = 0

    class FakePage:
        def __init__(self):
            self.title = ""
            self.theme = None
            self.theme_mode = None
            self.padding = None
            self.window = FakeWindow()
            self.on_keyboard_event = None
            self.controls = []
            self.overlay = []

        def add(self, *c):
            self.controls.extend(c)

        def update(self):
            pass

    page = FakePage()
    main_module.main(page)

    assert launched["called"] is False  # no Flet launch when a page is supplied
    assert page.title  # app constructed and configured the page
