"""Lock screen page - Password entry to unlock the vault.

Design: full-bleed brand gradient background, a frosted-glass card
holding the password form, and a glowing shield icon.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import flet as ft

from src.config import Config
from src.core.vault import Vault, VaultUnlockError
from src.ui.flet_compat import border_all, padding_all, show_snack_bar
from src.ui.theme import BRAND_GRADIENT


class LockPage(ft.Column):
    """Lock screen for vault authentication."""

    def __init__(
        self,
        vault: Vault,
        page: ft.Page,
        on_unlock: Optional[Callable] = None,
    ):
        super().__init__()
        self.vault = vault
        self.app_page = page
        self._on_unlock = on_unlock
        self._failed_attempts = 0
        self._locked_until: float | None = None
        self._is_creating = False

        # Glowing shield icon in a gradient circle
        self._shield_icon = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD, size=56, color=ft.Colors.WHITE),
            width=88,
            height=88,
            border_radius=44,
            gradient=BRAND_GRADIENT,
            alignment=ft.Alignment.CENTER,
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=24,
                    color=ft.Colors.with_opacity(0.45, "#6366F1"),
                    offset=ft.Offset(0, 8),
                ),
            ],
        )

        # App title area
        self._title = ft.Column(
            controls=[
                self._shield_icon,
                ft.Container(height=12),
                ft.Text(
                    "2FA Authenticator",
                    size=26,
                    weight=ft.FontWeight.W_800,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Your secure 2FA vault",
                    size=14,
                    color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

        # Password field
        self._password_field = ft.TextField(
            label="Master Password",
            hint_text="Enter your master password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=14,
            on_submit=self._on_submit,
            autofocus=True,
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)
            ),
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)
            ),
            focused_border_color=ft.Colors.WHITE,
            border_color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
        )

        # Confirm password (only for creation)
        self._confirm_field = ft.TextField(
            label="Confirm Password",
            hint_text="Re-enter your password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=14,
            on_submit=self._on_submit,
            visible=False,
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)
            ),
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)
            ),
            focused_border_color=ft.Colors.WHITE,
            border_color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
        )

        # Error message
        self._error_text = ft.Text(
            "",
            color="#FCA5A5",
            size=13,
            weight=ft.FontWeight.W_500,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

        # Submit button — bright pill-shaped gradient button
        self._submit_label = ft.Text(
            "Unlock", size=15, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE
        )
        self._submit_icon = ft.Icon(ft.Icons.LOCK_OPEN, size=18, color=ft.Colors.WHITE)
        self._submit_btn = ft.Container(
            content=ft.Row(
                controls=[self._submit_icon, self._submit_label],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            gradient=BRAND_GRADIENT,
            border_radius=14,
            padding=padding_all(14),
            alignment=ft.Alignment.CENTER,
            ink=True,
            on_click=self._on_submit,
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=16,
                    color=ft.Colors.with_opacity(0.35, "#6366F1"),
                    offset=ft.Offset(0, 6),
                ),
            ],
            animate_scale=ft.Animation(150),
            scale=1.0,
        )

        # Frosted glass form card
        self._form_card = ft.Container(
            content=ft.Column(
                controls=[
                    self._password_field,
                    self._confirm_field,
                    ft.Container(height=4),
                    self._error_text,
                    ft.Container(height=8),
                    self._submit_btn,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            width=360,
            padding=padding_all(24),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            border=border_all(1, ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
        )

        # Full gradient background wrapper — scrollable so content
        # stays accessible on short screens / landscape.
        self._bg = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=40),  # top breathing room
                    self._title,
                    ft.Container(height=36),
                    self._form_card,
                    ft.Container(height=40),  # bottom breathing room
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            gradient=BRAND_GRADIENT,
        )

        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        self.expand = True
        self.controls = [self._bg]

    def did_mount(self):
        """Check if vault exists and set up appropriate flow."""
        try:
            meta = self.vault._load_meta()
            if meta is None:
                self._is_creating = True
                self._submit_label.value = "Create Vault"
                self._submit_icon.name = ft.Icons.ADD
                self._confirm_field.visible = True
                self._password_field.label = "Set Master Password"
                self._password_field.hint_text = "Choose a strong password"
            else:
                self._is_creating = False
        except Exception:
            pass
        self.update()

    async def _on_submit(self, e) -> None:
        """Handle password submission."""
        self._submit_btn.scale = 0.96
        self.update()

        password = self._password_field.value

        if not password:
            self._show_error("Password is required")
            self._submit_btn.scale = 1.0
            self.update()
            return

        if self._locked_until is not None:
            remaining_seconds = int(self._locked_until - time.monotonic())
            if remaining_seconds > 0:
                self._show_error(
                    f"Too many failed attempts. Wait {remaining_seconds} seconds."
                )
                self._submit_btn.scale = 1.0
                self.update()
                return
            self._locked_until = None
            self._failed_attempts = 0

        if self._failed_attempts >= Config.MAX_UNLOCK_ATTEMPTS:
            self._locked_until = time.monotonic() + Config.UNLOCK_DELAY_SECONDS
            self._show_error(
                f"Too many failed attempts. Wait {Config.UNLOCK_DELAY_SECONDS} seconds."
            )
            self._submit_btn.scale = 1.0
            self.update()
            return

        try:
            if self._is_creating:
                await self._create_vault(password)
            else:
                await self._unlock_vault(password)
        finally:
            self._submit_btn.scale = 1.0
            self.update()

    async def _create_vault(self, password: str) -> None:
        confirm = self._confirm_field.value
        if password != confirm:
            self._show_error("Passwords do not match")
            return
        if len(password) < 8:
            self._show_error("Password must be at least 8 characters")
            return
        try:
            self.vault.create(password)
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text("Vault created successfully!"),
                    bgcolor=ft.Colors.GREEN,
                ),
            )
            if self._on_unlock:
                self._on_unlock()
        except Exception as ex:
            self._show_error(f"Failed to create vault: {ex}")

    async def _unlock_vault(self, password: str) -> None:
        try:
            self.vault.unlock(password)
            self._failed_attempts = 0
            if self._on_unlock:
                self._on_unlock()
        except VaultUnlockError:
            self._failed_attempts += 1
            remaining = Config.MAX_UNLOCK_ATTEMPTS - self._failed_attempts
            if remaining > 0:
                self._show_error(
                    f"Wrong password. {remaining} attempts remaining."
                )
            else:
                self._show_error(
                    f"Too many failed attempts. Wait {Config.UNLOCK_DELAY_SECONDS} seconds."
                )
                self._locked_until = time.monotonic() + Config.UNLOCK_DELAY_SECONDS
        except Exception as ex:
            self._show_error(f"Error: {ex}")

    def _show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = True
        self.update()

    def _clear_error(self) -> None:
        self._error_text.value = ""
        self._error_text.visible = False
