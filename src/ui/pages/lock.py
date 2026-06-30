"""Lock screen page - Password entry to unlock the vault."""

from __future__ import annotations

import time
from typing import Callable, Optional

import flet as ft

from src.config import Config
from src.core.vault import Vault, VaultUnlockError
from src.ui.flet_compat import button, padding_all, show_snack_bar


class LockPage(ft.Column):
    """Lock screen for vault authentication.

    Features:
    - Password entry with reveal toggle
    - Create new vault flow
    - Unlock existing vault flow
    - Failed attempt tracking with delay
    """

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

        # App title
        self._title = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.SECURITY,
                    size=64,
                    color=ft.Colors.BLUE,
                ),
                ft.Text(
                    "2FA Authenticator",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Your secure 2FA vault",
                    size=14,
                    color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        # Password field
        self._password_field = ft.TextField(
            label="Master Password",
            hint_text="Enter your master password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            on_submit=self._on_submit,
            autofocus=True,
        )

        # Confirm password (only for creation)
        self._confirm_field = ft.TextField(
            label="Confirm Password",
            hint_text="Re-enter your password",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            on_submit=self._on_submit,
            visible=False,
        )

        # Error message
        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=13,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

        # Submit button
        self._submit_btn = button(
            "Unlock",
            icon=ft.Icons.LOCK_OPEN,
            on_click=self._on_submit,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            expand=True,
        )

        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.alignment = ft.MainAxisAlignment.CENTER
        self.expand = True
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        self._title,
                        ft.Container(height=32),
                        self._password_field,
                        self._confirm_field,
                        self._error_text,
                        ft.Container(height=16),
                        ft.Row(
                            controls=[self._submit_btn],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                width=360,
                padding=padding_all(24),
            ),
        ]

    def did_mount(self):
        """Check if vault exists and set up appropriate flow."""
        try:
            meta = self.vault._load_meta()
            if meta is None:
                # New vault - show creation flow
                self._is_creating = True
                self._submit_btn.text = "Create Vault"
                self._submit_btn.icon = ft.Icons.ADD
                self._confirm_field.visible = True
                self._password_field.label = "Set Master Password"
                self._password_field.hint_text = "Choose a strong password"
            else:
                # Existing vault - show unlock flow
                self._is_creating = False
                self._submit_btn.text = "Unlock"
                self._submit_btn.icon = ft.Icons.LOCK_OPEN
                self._confirm_field.visible = False
        except Exception:
            pass
        self.update()

    async def _on_submit(self, e) -> None:
        """Handle password submission."""
        password = self._password_field.value

        if not password:
            self._show_error("Password is required")
            return

        # Check for too many failed attempts
        if self._locked_until is not None:
            remaining_seconds = int(self._locked_until - time.monotonic())
            if remaining_seconds > 0:
                self._show_error(
                    f"Too many failed attempts. Wait {remaining_seconds} seconds."
                )
                return
            self._locked_until = None
            self._failed_attempts = 0

        if self._failed_attempts >= Config.MAX_UNLOCK_ATTEMPTS:
            self._locked_until = time.monotonic() + Config.UNLOCK_DELAY_SECONDS
            self._show_error(
                f"Too many failed attempts. Wait {Config.UNLOCK_DELAY_SECONDS} seconds."
            )
            return

        if self._is_creating:
            await self._create_vault(password)
        else:
            await self._unlock_vault(password)

    async def _create_vault(self, password: str) -> None:
        """Create a new vault."""
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
        """Unlock an existing vault."""
        try:
            self.vault.unlock(password)
            self._failed_attempts = 0

            if self._on_unlock:
                self._on_unlock()

        except VaultUnlockError:
            self._failed_attempts += 1
            remaining = Config.MAX_UNLOCK_ATTEMPTS - self._failed_attempts

            if remaining > 0:
                self._show_error(f"Wrong password. {remaining} attempts remaining.")
            else:
                self._show_error(
                    f"Too many failed attempts. Wait {Config.UNLOCK_DELAY_SECONDS} seconds."
                )
                self._locked_until = time.monotonic() + Config.UNLOCK_DELAY_SECONDS

        except Exception as ex:
            self._show_error(f"Error: {ex}")

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        self._error_text.value = message
        self._error_text.visible = True
        self.update()

    def _clear_error(self) -> None:
        """Clear the error message."""
        self._error_text.value = ""
        self._error_text.visible = False
