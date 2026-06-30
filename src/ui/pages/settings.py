"""Settings page."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.config import Config
from src.core.vault import Vault
from src.ui.flet_compat import button, padding_only, padding_symmetric, set_clipboard, show_snack_bar


class SettingsPage(ft.Column):
    """Application settings page.

    Sections:
    - Security (auto-lock, clipboard clear)
    - GitHub (client ID/secret)
    - Data (backup, restore, import/export)
    - About
    """

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

        # Security settings
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

        # GitHub settings
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
            ft.Container(
                content=ft.Text(
                    "Settings",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                padding=padding_only(left=16, top=16, bottom=8),
            ),
            ft.ListView(
                controls=[
                    # Security section
                    self._section_header("Security", ft.Icons.SECURITY),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._auto_lock_dropdown,
                                self._clipboard_clear_dropdown,
                            ],
                            spacing=12,
                        ),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                    ),

                    # Change password
                    ft.Container(
                        content=button(
                            "Change Master Password",
                            icon=ft.Icons.LOCK_RESET,
                            on_click=self._change_password,
                        ),
                        padding=padding_symmetric(horizontal=16),
                    ),

                    ft.Divider(),

                    # GitHub section
                    self._section_header("GitHub", ft.Icons.CODE),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._github_client_id,
                                self._github_client_secret,
                                button(
                                    "Save GitHub Settings",
                                    icon=ft.Icons.SAVE,
                                    on_click=self._save_github_settings,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                    ),

                    ft.Divider(),

                    # Data section
                    self._section_header("Data", ft.Icons.STORAGE),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        button(
                                            "Export Backup",
                                            icon=ft.Icons.BACKUP,
                                            on_click=lambda _: self._on_backup() if self._on_backup else None,
                                            expand=True,
                                        ),
                                        button(
                                            "Import Backup",
                                            icon=ft.Icons.RESTORE,
                                            on_click=lambda _: self._on_restore() if self._on_restore else None,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=12,
                                ),
                                ft.OutlinedButton(
                                    "Export as URI List",
                                    icon=ft.Icons.LINK,
                                    on_click=self._export_uris,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                    ),

                    ft.Divider(),

                    # About section
                    self._section_header("About", ft.Icons.INFO),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(f"Version: {Config.APP_VERSION}"),
                                ft.Text("A secure 2FA authenticator with GitHub integration."),
                                ft.Text(
                                    "Open source under MIT License.",
                                    size=13,
                                    color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                    ),
                ],
                spacing=8,
                expand=True,
            ),
        ]

    def _section_header(self, title: str, icon: str) -> ft.Container:
        """Create a section header."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(icon, size=20, color=ft.Colors.BLUE),
                    ft.Text(
                        title,
                        size=16,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=8,
            ),
            padding=padding_only(left=16, top=12, bottom=4),
        )

    def _change_password(self, e) -> None:
        """Show change password dialog."""
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
            title=ft.Text("Change Master Password"),
            content=ft.Column(
                controls=[
                    old_pw_field,
                    new_pw_field,
                    confirm_pw_field,
                    error_text,
                ],
                spacing=12,
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dialog, "open", False) or self.app_page.update()),
                ft.TextButton("Change", on_click=_do_change),
            ],
        )

        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def _save_github_settings(self, e) -> None:
        """Save GitHub OAuth settings."""
        Config.save_settings(
            github_client_id=self._github_client_id.value or "",
            github_client_secret=self._github_client_secret.value or "",
            auto_lock_seconds=int(self._auto_lock_dropdown.value or Config.AUTO_LOCK_SECONDS),
            clipboard_clear_seconds=int(
                self._clipboard_clear_dropdown.value or Config.CLIPBOARD_CLEAR_SECONDS
            ),
        )

        show_snack_bar(
            self.app_page,
            ft.SnackBar(content=ft.Text("Settings saved")),
        )

    def _export_uris(self, e) -> None:
        """Export all accounts as URI list to clipboard."""
        try:
            from src.utils.export_import import export_uri_list
            accounts = self.vault.get_all_accounts()
            uri_text = export_uri_list(accounts)
            set_clipboard(self.app_page, uri_text)
            show_snack_bar(
                self.app_page,
                ft.SnackBar(content=ft.Text(f"Exported {len(accounts)} accounts to clipboard")),
            )
        except Exception as ex:
            show_snack_bar(
                self.app_page,
                ft.SnackBar(content=ft.Text(f"Export failed: {ex}"), bgcolor=ft.Colors.RED),
            )
