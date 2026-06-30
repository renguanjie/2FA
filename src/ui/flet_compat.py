"""Compatibility helpers for Flet API changes."""

from __future__ import annotations

from typing import Any

import flet as ft


def show_snack_bar(page: ft.Page, snack_bar: ft.SnackBar) -> None:
    """Show a snack bar on both legacy and current Flet versions."""
    legacy_show = getattr(page, "show_snack_bar", None)
    if callable(legacy_show):
        legacy_show(snack_bar)
        return

    page.overlay.append(snack_bar)
    snack_bar.open = True
    page.update()


def set_clipboard(page: ft.Page, text: str) -> None:
    """Set clipboard text on both legacy and current Flet versions."""
    legacy_set = getattr(page, "set_clipboard", None)
    if callable(legacy_set):
        legacy_set(text)
        return

    clipboard = getattr(page, "clipboard", None)
    if clipboard is None:
        raise RuntimeError("Flet clipboard service is not available")
    clipboard.set(text)


def get_clipboard(page: ft.Page) -> str | None:
    """Get clipboard text on both legacy and current Flet versions."""
    legacy_get = getattr(page, "get_clipboard", None)
    if callable(legacy_get):
        return legacy_get()

    clipboard = getattr(page, "clipboard", None)
    if clipboard is None:
        return None
    return clipboard.get()


def set_window_size(page: ft.Page, width: int, height: int) -> None:
    """Set initial window size across Flet versions when supported."""
    window = getattr(page, "window", None)
    if window is not None:
        window.width = width
        window.height = height
        return

    if hasattr(page, "width"):
        page.width = width
    if hasattr(page, "height"):
        page.height = height


def padding_all(value: int | float):
    """Create all-side padding across Flet versions."""
    factory = getattr(ft.padding, "all", None)
    if callable(factory):
        return factory(value)
    return ft.Padding(value, value, value, value)


def padding_only(
    *,
    left: int | float = 0,
    top: int | float = 0,
    right: int | float = 0,
    bottom: int | float = 0,
):
    """Create per-side padding across Flet versions."""
    factory = getattr(ft.padding, "only", None)
    if callable(factory):
        return factory(left=left, top=top, right=right, bottom=bottom)
    return ft.Padding(left, top, right, bottom)


def padding_symmetric(
    *,
    horizontal: int | float = 0,
    vertical: int | float = 0,
):
    """Create symmetric padding across Flet versions."""
    factory = getattr(ft.padding, "symmetric", None)
    if callable(factory):
        return factory(horizontal=horizontal, vertical=vertical)
    return ft.Padding(horizontal, vertical, horizontal, vertical)


def border_all(width: int | float, color):
    """Create all-side border across Flet versions."""
    factory = getattr(ft.border, "all", None)
    if callable(factory):
        return factory(width, color)

    side = ft.BorderSide(width=width, color=color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def button(*args: Any, **kwargs: Any):
    """Create a filled button across Flet versions.

    Flet 0.80 renamed ``ElevatedButton`` to ``Button`` (removal in 1.0).
    Prefer the new name and fall back to the legacy one on older Flet.
    """
    factory = getattr(ft, "Button", None) or ft.ElevatedButton
    return factory(*args, **kwargs)


def safe_update(control: Any) -> None:
    """Update a control only when it is already attached to a page."""
    try:
        control.update()
    except AssertionError:
        pass
