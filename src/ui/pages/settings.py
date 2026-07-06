"""Settings page.

Design: gradient page header, card-based sections with
colourful icon badges, and pill-shaped action buttons.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.config import Config
from src.core.vault import Vault
from src.ui.flet_compat import (
    border_all,
    button,
    padding_all,
    set_clipboard,
    show_snack_bar,
)
from src.ui.theme import BRAND_GRADIENT


class SettingsPage(ft.Column):
    """Application settings page."""

    def __init__(
        self,
        vault: Vault,
        page: ft.Page,
        on_backup: Optional[Callable] = None,
        on_restore: Optional[Callable] = None,
    ):
        super().__init__()
        self.vault = vault
        self.app_page = page
        self._on_backup = on_backup
        self._on_restore = on_restore

        self._auto_lock_dropdown = ft.Dropdown(
            label="Auto-lock after",
            value=str(Config.AUTO_LOCK_SECONDS),
            options=[
                ft.dropdown.Option("60", "1 minute"),
                ft.dropdown.Option("300", "5 minutes"),
                ft.dropdown.Option("600", "10 minutes"),
                ft.dropdown.Option("1800", "30 minutes"),
                ft.dropdown.Option("0", "Never"),
            ],
            border_radius=12,
            width=200,
        )
        self._clipboard_clear_dropdown = ft.Dropdown(
            label="Clear clipboard after",
            value=str(Config.CLIPBOARD_CLEAR_SECONDS),
            options=[
                ft.dropdown.Option("10", "10 seconds"),
                ft.dropdown.Option("30", "30 seconds"),
                ft.dropdown.Option("60", "1 minute"),
                ft.dropdown.Option("0", "Never"),
            ],
            border_radius=12,
            width=200,
        )

        self._github_client_id = ft.TextField(
            label="GitHub Client ID",
            value=Config.GITHUB_CLIENT_ID,
            border_radius=12,
            hint_text="Your GitHub OAuth App client ID",
        )
        self._github_client_secret = ft.TextField(
            label="GitHub Client Secret",
            value=Config.GITHUB_CLIENT_SECRET,
            border_radius=12,
            password=True,
            can_reveal_password=True,
            hint_text="Your GitHub OAuth App client secret",
        )

        self.expand = True
        self.controls = [
            # Gradient header
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Settings",
                                    size=22,
                                    weight=ft.FontWeight.W_800,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Customise your vault",
                                    size=12,
                                    color=ft.Colors.with_opacity(
                                        0.8, ft.Colors.WHITE
                                    ),
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.SETTINGS,
                                size=22,
                                color=ft.Colors.WHITE,
                            ),
                            width=38,
                            height=38,
                            border_radius=12,
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            alignment=ft.Alignment.CENTER,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(16, 16, 16, 16),
                gradient=BRAND_GRADIENT,
                border_radius=ft.BorderRadius(0, 0, 20, 20),
            ),
            ft.Container(height=8),
            ft.ListView(
                controls=[
                    self._card_section(
                        icon=ft.Icons.SECURITY,
                        icon_color="#6366F1",
                        title="Security",
                        controls=[
                            self._auto_lock_dropdown,
                            self._clipboard_clear_dropdown,
                        ],
                    ),
                    self._card_section(
                        icon=ft.Icons.LOCK_RESET,
                        icon_color="#8B5CF6",
                        title="Password",
                        controls=[
                            button(
                                "Change Master Password",
                                icon=ft.Icons.LOCK_RESET,
                                on_click=self._change_password,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                        ],
                    ),
                    self._card_section(
                        icon=ft.Icons.CODE,
                        icon_color="#1B2838",
                        title="GitHub",
                        controls=[
                            self._github_client_id,
                            self._github_client_secret,
                            button(
                                "Save GitHub Settings",
                                icon=ft.Icons.SAVE,
                                on_click=self._save_github_settings,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                        ],
                    ),
                    self._card_section(
                        icon=ft.Icons.STORAGE,
                        icon_color="#06B6D4",
                        title="Data",
                        controls=[
                            ft.Row(
                                controls=[
                                    button(
                                        "Export Backup",
                                        icon=ft.Icons.BACKUP,
                                        on_click=lambda _: self._on_backup()
                                        if self._on_backup
                                        else None,
                                        expand=True,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(
                                                radius=12
                                            ),
                                        ),
                                    ),
                                    button(
                                        "Import Backup",
                                        icon=ft.Icons.RESTORE,
                                        on_click=lambda _: self._on_restore()
                                        if self._on_restore
                                        else None,
                                        expand=True,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(
                                                radius=12
                                            ),
                                        ),
                                    ),
                                ],
                                spacing=12,
                            ),
                            ft.OutlinedButton(
                                "Export as URI List",
                                icon=ft.Icons.LINK,
                                on_click=self._export_uris,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                        ],
                    ),
                    self._card_section(
                        icon=ft.Icons.INFO,
                        icon_color="#10B981",
                        title="About",
                        controls=[
                            ft.Text(
                                f"Version {Config.APP_VERSION}",
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                "A secure 2FA authenticator with GitHub integration.",
                                size=13,
                                color=ft.Colors.with_opacity(
                                    0.6, ft.Colors.ON_SURFACE
                                ),
                            ),
                            ft.Text(
                                "Open source under MIT License.",
                                size=12,
                                color=ft.Colors.with_opacity(
                                    0.45, ft.Colors.ON_SURFACE
                                ),
                            ),
                        ],
                    ),
                ],
                spacing=10,
                expand=True,
            ),
        ]

    def _card_section(
        self,
        *,
        icon: str,
        icon_color: str,
        title: str,
        controls: list,
    ) -> ft.Container:
        """Render a titled card section with an icon badge."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(icon, size=18, color=icon_color),
                                width=36,
                                height=36,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Text(title, size=15, weight=ft.FontWeight.W_700),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    ft.Column(controls=controls, spacing=12),
                ],
                spacing=0,
            ),
            padding=padding_all(16),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
            border=border_all(1, ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)),
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
                    offset=ft.Offset(0, 3),
                ),
            ],
            margin=ft.Margin(12, 0, 12, 0),
        )

    def _change_password(self, e) -> None:
        old_pw_field = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )
        new_pw_field = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )
        confirm_pw_field = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )

        def _do_change(e):
            if new_pw_field.value != confirm_pw_field.value:
                error_text.value = "Passwords do not match"
                error_text.visible = True
                self.app_page.update()
                return
            try:
                self.vault.change_password(old_pw_field.value, new_pw_field.value)
                dialog.open = False
                show_snack_bar(
                    self.app_page,
                    ft.SnackBar(content=ft.Text("Password changed successfully")),
                )
            except Exception as ex:
                error_text.value = f"Error: {ex}"
                error_text.visible = True
            self.app_page.update()

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        dialog = ft.AlertDialog(
            title=ft.Text("Change Master Password", weight=ft.FontWeight.W_700),
            content=ft.Column(
                controls=[old_pw_field, new_pw_field, confirm_pw_field, error_text],
                spacing=12,
                tight=True,
            ),
            shape=ft.RoundedRectangleBorder(radius=16),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: setattr(dialog, "open", False)
                    or self.app_page.update(),
                ),
                ft.TextButton("Change", on_click=_do_change),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def _save_github_settings(self, e) -> None:
        Config.save_settings(
            github_client_id=self._github_client_id.value or "",
            github_client_secret=self._github_client_secret.value or "",
            auto_lock_seconds=int(
                self._auto_lock_dropdown.value or Config.AUTO_LOCK_SECONDS
            ),
            clipboard_clear_seconds=int(
                self._clipboard_clear_dropdown.value
                or Config.CLIPBOARD_CLEAR_SECONDS
            ),
        )
        show_snack_bar(
            self.app_page,
            ft.SnackBar(content=ft.Text("Settings saved")),
        )

    def _export_uris(self, e) -> None:
        try:
            from src.utils.export_import import export_uri_list

            accounts = self.vault.get_all_accounts()
            uri_text = export_uri_list(accounts)
            set_clipboard(self.app_page, uri_text)
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text(
                        f"Exported {len(accounts)} accounts to clipboard"
                    )
                ),
            )
        except Exception as ex:
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text(f"Export failed: {ex}"),
                    bgcolor=ft.Colors.RED,
                ),
            )
