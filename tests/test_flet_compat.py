"""Tests for Flet API compatibility helpers."""

import flet as ft

from src.ui.flet_compat import get_clipboard, set_clipboard, show_snack_bar


class ModernClipboard:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class ModernPage:
    def __init__(self):
        self.clipboard = ModernClipboard()
        self.overlay = []
        self.updated = False

    def update(self):
        self.updated = True


class LegacyPage:
    def __init__(self):
        self.value = ""
        self.snack = None

    def set_clipboard(self, value):
        self.value = value

    def get_clipboard(self):
        return self.value

    def show_snack_bar(self, snack):
        self.snack = snack


def test_clipboard_helpers_support_modern_flet_api():
    page = ModernPage()

    set_clipboard(page, "123456")

    assert get_clipboard(page) == "123456"


def test_clipboard_helpers_support_legacy_flet_api():
    page = LegacyPage()

    set_clipboard(page, "654321")

    assert get_clipboard(page) == "654321"


def test_show_snack_bar_supports_modern_overlay_api():
    page = ModernPage()
    snack = ft.SnackBar(content=ft.Text("Saved"))

    show_snack_bar(page, snack)

    assert page.overlay == [snack]
    assert snack.open is True
    assert page.updated is True


def test_show_snack_bar_supports_legacy_api():
    page = LegacyPage()
    snack = ft.SnackBar(content=ft.Text("Saved"))

    show_snack_bar(page, snack)

    assert page.snack is snack
