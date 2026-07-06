"""Backup and restore page.

Design: gradient header, card-based sections with icon badges,
pill-shaped action buttons.
"""

from __future__ import annotations

import flet as ft

from src.core.vault import Vault
from src.ui.flet_compat import (
    border_all,
    button,
    padding_all,
    set_clipboard,
    show_snack_bar,
)
from src.ui.theme import BRAND_GRADIENT
from src.utils.export_import import export_json, export_uri_list, import_json


class BackupPage(ft.Column):
    """Backup and restore page."""

    def __init__(self, vault: Vault, page: ft.Page):
        super().__init__()
        self.vault = vault
        self.app_page = page

        self.expand = True
        self.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "Backup & Restore",
                                    size=22,
                                    weight=ft.FontWeight.W_800,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Keep your vault safe",
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
                                ft.Icons.CLOUD_DONE,
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
                        icon=ft.Icons.BACKUP,
                        icon_color="#10B981",
                        title="Export",
                        controls=[
                            button(
                                "Export Encrypted Backup",
                                icon=ft.Icons.ENHANCED_ENCRYPTION,
                                on_click=self._export_encrypted,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                            button(
                                "Export as JSON",
                                icon=ft.Icons.CODE,
                                on_click=self._export_json,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                            button(
                                "Copy URI List to Clipboard",
                                icon=ft.Icons.LINK,
                                on_click=self._export_uris,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                        ],
                    ),
                    self._card_section(
                        icon=ft.Icons.RESTORE,
                        icon_color="#06B6D4",
                        title="Import",
                        controls=[
                            button(
                                "Import Encrypted Backup",
                                icon=ft.Icons.LOCK_OPEN,
                                on_click=self._import_encrypted,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                            button(
                                "Import from JSON File",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=self._import_json_file,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                            ),
                            button(
                                "Import from URI List",
                                icon=ft.Icons.CONTENT_PASTE_GO,
                                on_click=self._import_uris,
                                expand=True,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
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

    def _export_encrypted(self, e) -> None:
        pw_field = ft.TextField(
            label="Backup Password",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )

        def _do_export(e):
            if not pw_field.value:
                return
            try:
                data = self.vault.export_encrypted_backup(pw_field.value)

                def _on_save(result: ft.FilePickerResultEvent):
                    if result.path:
                        with open(result.path, "wb") as f:
                            f.write(data)
                        show_snack_bar(
                            self.app_page,
                            ft.SnackBar(
                                content=ft.Text("Backup exported successfully")
                            ),
                        )
                    dialog.open = False
                    self.app_page.update()

                file_picker = ft.FilePicker(on_result=_on_save)
                self.app_page.overlay.append(file_picker)
                self.app_page.update()
                file_picker.save_file(
                    dialog_title="Save Backup",
                    file_name="two_fa_backup.bin",
                    file_type=ft.FilePickerFileType.CUSTOM,
                    allowed_extensions=["bin"],
                )
            except Exception as ex:
                show_snack_bar(
                    self.app_page,
                    ft.SnackBar(
                        content=ft.Text(f"Export failed: {ex}"),
                        bgcolor=ft.Colors.RED,
                    ),
                )

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Export Encrypted Backup", weight=ft.FontWeight.W_700
            ),
            content=ft.Column(
                controls=[
                    ft.Text("Set a password to encrypt your backup:"),
                    pw_field,
                ],
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
                ft.TextButton("Export", on_click=_do_export),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def _export_json(self, e) -> None:
        try:
            accounts = self.vault.get_all_accounts()
            json_str = export_json(accounts)
            set_clipboard(self.app_page, json_str)
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text(
                        f"Exported {len(accounts)} accounts to clipboard as JSON"
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

    def _export_uris(self, e) -> None:
        try:
            accounts = self.vault.get_all_accounts()
            uri_text = export_uri_list(accounts)
            set_clipboard(self.app_page, uri_text)
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text(
                        f"Exported {len(accounts)} URIs to clipboard"
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

    def _import_encrypted(self, e) -> None:
        pw_field = ft.TextField(
            label="Backup Password",
            password=True,
            can_reveal_password=True,
            border_radius=12,
        )

        def _do_import(e):
            if not pw_field.value:
                return

            def _on_pick(result: ft.FilePickerResultEvent):
                if result.files:
                    try:
                        with open(result.files[0].path, "rb") as f:
                            data = f.read()
                        count = self.vault.import_encrypted_backup(
                            data, pw_field.value
                        )
                        show_snack_bar(
                            self.app_page,
                            ft.SnackBar(
                                content=ft.Text(
                                    f"Imported {count} accounts successfully"
                                ),
                                bgcolor=ft.Colors.GREEN,
                            ),
                        )
                    except Exception as ex:
                        show_snack_bar(
                            self.app_page,
                            ft.SnackBar(
                                content=ft.Text(f"Import failed: {ex}"),
                                bgcolor=ft.Colors.RED,
                            ),
                        )
                dialog.open = False
                self.app_page.update()

            file_picker = ft.FilePicker(on_result=_on_pick)
            self.app_page.overlay.append(file_picker)
            self.app_page.update()
            file_picker.pick_files(
                dialog_title="Select Backup File",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["bin"],
            )

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Import Encrypted Backup", weight=ft.FontWeight.W_700
            ),
            content=ft.Column(
                controls=[
                    ft.Text("Enter the backup password:"),
                    pw_field,
                ],
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
                ft.TextButton("Import", on_click=_do_import),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def _import_json_file(self, e) -> None:
        def _on_pick(result: ft.FilePickerResultEvent):
            if result.files:
                try:
                    with open(result.files[0].path, "r") as f:
                        json_str = f.read()
                    accounts = import_json(json_str)
                    for acc in accounts:
                        self.vault.add_account(acc)
                    show_snack_bar(
                        self.app_page,
                        ft.SnackBar(
                            content=ft.Text(
                                f"Imported {len(accounts)} accounts"
                            ),
                            bgcolor=ft.Colors.GREEN,
                        ),
                    )
                except Exception as ex:
                    show_snack_bar(
                        self.app_page,
                        ft.SnackBar(
                            content=ft.Text(f"Import failed: {ex}"),
                            bgcolor=ft.Colors.RED,
                        ),
                    )

        file_picker = ft.FilePicker(on_result=_on_pick)
        self.app_page.overlay.append(file_picker)
        self.app_page.update()
        file_picker.pick_files(
            dialog_title="Select JSON File",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
        )

    def _import_uris(self, e) -> None:
        uri_field = ft.TextField(
            label="URI List",
            hint_text="Paste otpauth:// URIs (one per line)",
            multiline=True,
            min_lines=4,
            max_lines=8,
            border_radius=12,
        )

        def _do_import(e):
            try:
                from src.utils.export_import import import_uri_list

                accounts = import_uri_list(uri_field.value)
                for acc in accounts:
                    self.vault.add_account(acc)
                dialog.open = False
                show_snack_bar(
                    self.app_page,
                    ft.SnackBar(
                        content=ft.Text(
                            f"Imported {len(accounts)} accounts"
                        ),
                        bgcolor=ft.Colors.GREEN,
                    ),
                )
            except Exception as ex:
                show_snack_bar(
                    self.app_page,
                    ft.SnackBar(
                        content=ft.Text(f"Import failed: {ex}"),
                        bgcolor=ft.Colors.RED,
                    ),
                )
            self.app_page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Import from URI List", weight=ft.FontWeight.W_700),
            content=ft.Column(
                controls=[
                    ft.Text("Paste otpauth:// URIs:"),
                    uri_field,
                ],
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
                ft.TextButton("Import", on_click=_do_import),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()
