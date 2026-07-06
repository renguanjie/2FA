"""Add account page - Manual input, QR scan, or URI import.

Design: gradient header, colourful segmented switcher, and
rounded form fields.
"""

from __future__ import annotations

import uuid
from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPType, Algorithm
from src.core.uri_parser import parse_otpauth_uri
from src.core.vault import Vault
from src.ui.flet_compat import (
    button,
    padding_all,
    padding_only,
    padding_symmetric,
    show_snack_bar,
)
from src.ui.theme import BRAND_GRADIENT

try:
    from flet_qr_scanner import FletQrScanner

    _HAS_CAMERA_SCANNER = True
except ImportError:  # pragma: no cover
    FletQrScanner = None
    _HAS_CAMERA_SCANNER = False


class AddAccountPage(ft.Column):
    """Page for adding a new OTP account."""

    def __init__(
        self,
        vault: Vault,
        page: ft.Page,
        on_done: Optional[Callable] = None,
    ):
        super().__init__()
        self.vault = vault
        self.app_page = page
        self._on_done = on_done

        # Form fields
        self._issuer_field = ft.TextField(
            label="Issuer (e.g. GitHub)",
            prefix_icon=ft.Icons.BUSINESS,
            border_radius=12,
        )
        self._name_field = ft.TextField(
            label="Account name (e.g. user@email.com)",
            prefix_icon=ft.Icons.PERSON,
            border_radius=12,
        )
        self._secret_field = ft.TextField(
            label="Secret key (Base32)",
            prefix_icon=ft.Icons.KEY,
            border_radius=12,
            password=True,
            can_reveal_password=True,
        )
        self._algorithm_dropdown = ft.Dropdown(
            label="Algorithm",
            value="SHA1",
            options=[
                ft.dropdown.Option("SHA1"),
                ft.dropdown.Option("SHA256"),
                ft.dropdown.Option("SHA512"),
            ],
            border_radius=12,
            width=150,
        )
        self._digits_dropdown = ft.Dropdown(
            label="Digits",
            value="6",
            options=[
                ft.dropdown.Option("6"),
                ft.dropdown.Option("7"),
                ft.dropdown.Option("8"),
            ],
            border_radius=12,
            width=100,
        )
        self._period_field = ft.TextField(
            label="Period (sec)",
            value="30",
            border_radius=12,
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        self._type_dropdown = ft.Dropdown(
            label="Type",
            value="totp",
            options=[
                ft.dropdown.Option("totp", "TOTP"),
                ft.dropdown.Option("hotp", "HOTP"),
            ],
            border_radius=12,
            width=120,
        )

        self._uri_field = ft.TextField(
            label="otpauth:// URI",
            hint_text="Paste otpauth://totp/...",
            prefix_icon=ft.Icons.LINK,
            border_radius=12,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        # Method views — each tab Container has expand=True so it fills
        # the _method_content bounds, letting the inner scroll Column
        # properly scroll when content overflows.
        self._manual_tab = ft.Container(
            content=ft.Column(
                controls=[
                    self._issuer_field,
                    self._name_field,
                    self._secret_field,
                    ft.Row(
                        controls=[
                            self._algorithm_dropdown,
                            self._digits_dropdown,
                            self._period_field,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self._type_dropdown,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=padding_all(16),
            expand=True,
        )
        self._qr_tab = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.QR_CODE_SCANNER,
                            size=48,
                            color=ft.Colors.WHITE,
                        ),
                        width=80,
                        height=80,
                        border_radius=24,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=["#6366F1", "#06B6D4"],
                        ),
                        alignment=ft.Alignment.CENTER,
                        shadow=[
                            ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=16,
                                color=ft.Colors.with_opacity(0.3, "#6366F1"),
                                offset=ft.Offset(0, 6),
                            ),
                        ],
                    ),
                    ft.Text(
                        "Scan an otpauth QR code",
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                        color=ft.Colors.with_opacity(
                            0.55, ft.Colors.ON_SURFACE
                        ),
                    ),
                    button(
                        "Scan with Camera",
                        icon=ft.Icons.PHOTO_CAMERA,
                        on_click=self._scan_camera,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                    button(
                        "Select Image",
                        icon=ft.Icons.IMAGE,
                        on_click=self._pick_image,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
                expand=True,
            ),
            padding=padding_all(32),
            expand=True,
        )
        self._uri_tab = ft.Container(
            content=ft.Column(
                controls=[
                    self._uri_field,
                    button(
                        "Import from URI",
                        icon=ft.Icons.IMPORT_EXPORT,
                        on_click=self._import_uri,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                ],
                spacing=12,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=padding_all(16),
            expand=True,
        )

        # Method views list
        self._method_views = [self._manual_tab, self._qr_tab, self._uri_tab]
        self._method_content = ft.Container(
            content=self._manual_tab, expand=True
        )

        # Colourful segmented switcher
        segment_data = [
            ("Manual", ft.Icons.EDIT, "#6366F1"),
            ("Scan QR", ft.Icons.QR_CODE_SCANNER, "#8B5CF6"),
            ("Paste URI", ft.Icons.CONTENT_PASTE, "#06B6D4"),
        ]
        self._segment_buttons: list[ft.Container] = []
        for idx, (label, icon, color) in enumerate(segment_data):
            seg = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, size=18, color=ft.Colors.WHITE),
                        ft.Text(
                            label,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                on_click=lambda e, i=idx: self._select_method(i),
                padding=padding_symmetric(horizontal=10, vertical=10),
                border_radius=12,
                ink=True,
                expand=True,
                bgcolor=color,
                opacity=1.0 if idx == 0 else 0.45,
                animate_opacity=ft.Animation(200),
            )
            self._segment_buttons.append(seg)

        self._method_bar = ft.Container(
            content=ft.Row(controls=self._segment_buttons, spacing=6),
            padding=ft.Padding(6, 6, 6, 6),
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.ON_SURFACE),
            border_radius=16,
            margin=ft.Margin(12, 0, 12, 0),
        )

        # Error text
        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=13,
            weight=ft.FontWeight.W_500,
            visible=False,
        )

        # Save button
        self._save_btn = button(
            "Save Account",
            icon=ft.Icons.SAVE,
            on_click=self._save_manual,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )
        self._manual_tab.content.controls.append(
            ft.Container(
                content=self._save_btn, padding=padding_only(top=8)
            )
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
                                    "Add Account",
                                    size=22,
                                    weight=ft.FontWeight.W_800,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Scan, paste, or type manually",
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
                                ft.Icons.ADD_CIRCLE,
                                size=22,
                                color=ft.Colors.WHITE,
                            ),
                            width=38,
                            height=38,
                            border_radius=12,
                            bgcolor=ft.Colors.with_opacity(
                                0.2, ft.Colors.WHITE
                            ),
                            alignment=ft.Alignment.CENTER,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(16, 16, 16, 16),
                gradient=BRAND_GRADIENT,
                border_radius=ft.BorderRadius(0, 0, 20, 20),
            ),
            ft.Container(height=12),
            self._method_bar,
            ft.Container(
                content=self._error_text,
                padding=padding_symmetric(horizontal=16),
            ),
            self._method_content,
        ]

    def _select_method(self, index: int) -> None:
        self._method_content.content = self._method_views[index]
        for i, seg in enumerate(self._segment_buttons):
            seg.opacity = 1.0 if i == index else 0.45
        self._clear_error()
        self.update()

    def _show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = True
        self.update()

    def _clear_error(self) -> None:
        self._error_text.value = ""
        self._error_text.visible = False

    def _save_manual(self, e) -> None:
        self._clear_error()
        issuer = self._issuer_field.value.strip()
        name = self._name_field.value.strip()
        secret = self._secret_field.value.strip().upper().replace(" ", "")

        if not secret:
            self._show_error("Secret key is required")
            return
        if not issuer:
            issuer = "Unknown"
        if not name:
            name = "Account"

        try:
            import base64

            pad = 8 - len(secret) % 8
            if pad != 8:
                secret += "=" * pad
            base64.b32decode(secret)
        except Exception:
            self._show_error("Invalid Base32 secret key")
            return

        secret = secret.rstrip("=")
        account = OTPAccount(
            id=str(uuid.uuid4()),
            issuer=issuer,
            name=name,
            secret=secret,
            otp_type=OTPType(self._type_dropdown.value),
            algorithm=Algorithm(self._algorithm_dropdown.value),
            digits=int(self._digits_dropdown.value),
            period=int(self._period_field.value or "30"),
            is_github="github" in issuer.lower(),
        )

        try:
            self.vault.add_account(account)
            if self._on_done:
                self._on_done()
        except Exception as ex:
            self._show_error(f"Failed to save: {ex}")

    def _import_uri(self, e) -> None:
        self._clear_error()
        uri = self._uri_field.value.strip()
        if not uri:
            self._show_error("Please paste an otpauth:// URI")
            return
        if not uri.startswith("otpauth://"):
            self._show_error("URI must start with otpauth://")
            return
        try:
            account = parse_otpauth_uri(uri)
            self.vault.add_account(account)
            if self._on_done:
                self._on_done()
        except ValueError as ex:
            self._show_error(f"Invalid URI: {ex}")
        except Exception as ex:
            self._show_error(f"Failed to import: {ex}")

    def _scan_camera(self, e) -> None:
        if not _HAS_CAMERA_SCANNER:
            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text(
                        "Camera scanning is only available in the mobile app build. "
                        "Use 'Select Image' or paste a URI instead."
                    )
                ),
            )
            return

        scanner = FletQrScanner(
            facing="back",
            on_detect=self._on_qr_detected,
            expand=True,
        )
        self._scan_dialog = ft.AlertDialog(
            title=ft.Text("Scan QR code", weight=ft.FontWeight.W_700),
            content=ft.Container(width=300, height=300, content=scanner),
            shape=ft.RoundedRectangleBorder(radius=16),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self._close_scan_dialog(),
                ),
            ],
        )
        self.app_page.overlay.append(self._scan_dialog)
        self._scan_dialog.open = True
        self.app_page.update()

    def _close_scan_dialog(self) -> None:
        dialog = getattr(self, "_scan_dialog", None)
        if dialog is not None:
            dialog.open = False
            self._scan_dialog = None
            self.app_page.update()

    def _on_qr_detected(self, e) -> None:
        uri = (getattr(e, "data", None) or "").strip()
        self._close_scan_dialog()
        if not uri.startswith("otpauth://"):
            self._show_error("Scanned code is not an otpauth:// URI")
            return
        try:
            account = parse_otpauth_uri(uri)
            self.vault.add_account(account)
            if self._on_done:
                self._on_done()
        except ValueError as ex:
            self._show_error(f"Invalid QR: {ex}")
        except Exception as ex:
            self._show_error(f"Failed to add account: {ex}")

    def _pick_image(self, e) -> None:
        """Open file picker to select a QR code image.

        Handles both regular file paths and Android content URIs by
        falling back to byte-level decoding when ``Image.open(path)``
        fails.
        """

        async def _on_result(result: ft.FilePickerResultEvent):
            if not result.files:
                return
            picked = result.files[0]
            path_str = getattr(picked, "path", None) or ""
            try:
                from src.core.qr import scan_qr_from_bytes, scan_qr_from_image

                # Try path-based decode first (desktop / cached Android)
                if path_str:
                    from pathlib import Path

                    image_path = Path(path_str)
                    if image_path.is_file():
                        uri = scan_qr_from_image(image_path)
                        if uri and uri.startswith("otpauth://"):
                            account = parse_otpauth_uri(uri)
                            self.vault.add_account(account)
                            if self._on_done:
                                self._on_done()
                            return

                # Fallback: read raw bytes and decode in-memory
                # (handles Android content:// URIs or inaccessible paths)
                if path_str:
                    with open(path_str, "rb") as f:
                        raw = f.read()
                    uri = scan_qr_from_bytes(raw)
                    if uri and uri.startswith("otpauth://"):
                        account = parse_otpauth_uri(uri)
                        self.vault.add_account(account)
                        if self._on_done:
                            self._on_done()
                        return
                    # File exists but no QR found
                    self._show_error(
                        "No valid otpauth QR code found in image"
                    )
                    return

                self._show_error("Could not read the selected image")
            except FileNotFoundError:
                self._show_error("Selected image was not found on disk")
            except Exception as ex:
                self._show_error(f"Failed to scan QR: {ex}")

        file_picker = ft.FilePicker(on_result=_on_result)
        self.app_page.overlay.append(file_picker)
        self.app_page.update()
        file_picker.pick_files(
            dialog_title="Select QR Code Image",
            file_type=ft.FilePickerFileType.ANY,
        )
