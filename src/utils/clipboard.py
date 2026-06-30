"""Clipboard utilities with auto-clear support."""

from __future__ import annotations

import threading

import flet as ft

from src.config import Config
from src.ui.flet_compat import get_clipboard, set_clipboard, show_snack_bar


def copy_to_clipboard(page: ft.Page, text: str, clear_after: int | None = None) -> None:
    """Copy text to clipboard with optional auto-clear.

    Args:
        page: Flet page instance.
        text: Text to copy.
        clear_after: Seconds to wait before clearing (0 to disable).
    """
    if clear_after is None:
        clear_after = Config.CLIPBOARD_CLEAR_SECONDS

    set_clipboard(page, text)
    show_snack_bar(
        page,
        ft.SnackBar(
            content=ft.Text("Copied to clipboard"),
            duration=2000,
        ),
    )

    if clear_after > 0:
        def _clear():
            current = get_clipboard(page)
            if current == text:
                set_clipboard(page, "")

        timer = threading.Timer(clear_after, _clear)
        timer.daemon = True
        timer.start()
