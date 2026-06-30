"""Tests for the camera-scan flow on the Add Account page.

These exercise the Python side of the live-camera integration (dialog wiring +
detect handler) without a real camera; the native scanner is only active in
mobile builds.
"""

import flet as ft

from src.ui.pages import add_account as aa
from src.ui.pages.add_account import AddAccountPage

URI = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub"


class FakePage:
    def __init__(self):
        self.overlay = []

    def update(self):
        pass


class FakeVault:
    def __init__(self):
        self.added = []

    def add_account(self, account):
        self.added.append(account)


def _make_page():
    vault = FakeVault()
    done = {"called": False}
    page = AddAccountPage(vault=vault, page=FakePage(), on_done=lambda: done.__setitem__("called", True))
    page.update = lambda: None  # control isn't attached to a real page
    return page, vault, done


def test_extension_is_importable():
    # Installed as an editable dependency for the build; must import cleanly.
    assert aa._HAS_CAMERA_SCANNER is True
    assert aa.FletQrScanner is not None


def test_scan_camera_opens_dialog_with_scanner():
    page, _, _ = _make_page()
    page._scan_camera(None)

    assert page.app_page.overlay, "a dialog should be added to the page overlay"
    dialog = page.app_page.overlay[-1]
    assert isinstance(dialog, ft.AlertDialog)
    assert dialog.open is True
    # The dialog content holds the native scanner control with our detect handler.
    scanner = dialog.content.content
    assert isinstance(scanner, aa.FletQrScanner)
    assert scanner.on_detect == page._on_qr_detected


def test_detect_valid_uri_adds_account_and_closes():
    page, vault, done = _make_page()
    page._scan_camera(None)

    event = type("E", (), {"data": URI})()
    page._on_qr_detected(event)

    assert len(vault.added) == 1
    assert vault.added[0].secret == "JBSWY3DPEHPK3PXP"
    assert done["called"] is True
    # Dialog closed after a successful scan.
    assert page._scan_dialog is None


def test_detect_non_otpauth_is_rejected():
    page, vault, _ = _make_page()
    page._scan_camera(None)

    event = type("E", (), {"data": "https://example.com"})()
    page._on_qr_detected(event)

    assert vault.added == []
    assert page._error_text.visible is True
    assert page._scan_dialog is None  # dialog still closed


def test_scan_camera_without_extension_shows_message(monkeypatch):
    # Simulate a plain desktop install where the extension is absent.
    monkeypatch.setattr(aa, "_HAS_CAMERA_SCANNER", False)
    page, _, _ = _make_page()
    page._scan_camera(None)
    # No scanner dialog is opened; a snackbar message is shown instead.
    assert not any(isinstance(o, ft.AlertDialog) for o in page.app_page.overlay)
