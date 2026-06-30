"""Add account page - Manual input, QR scan, or URI import."""

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

try:
    # Native live-camera scanner extension (available in Android/iOS builds).
    from flet_qr_scanner import FletQrScanner

    _HAS_CAMERA_SCANNER = True
except ImportError:  # pragma: no cover - extension absent on plain desktop installs
    FletQrScanner = None
    _HAS_CAMERA_SCANNER = False


class AddAccountPage(ft.Column):
    """Page for adding a new OTP account.

    Supports three methods:
    1. Manual entry (issuer, name, secret)
    2. Scan QR code
    3. Paste otpauth:// URI
    """

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

        # Manual entry fields
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

        # URI input
        self._uri_field = ft.TextField(
            label="otpauth:// URI",
            hint_text="Paste otpauth://totp/...",
            prefix_icon=ft.Icons.LINK,
            border_radius=12,
            multiline=True,
            min_lines=2,
            max_lines=4,
        )

        # Tabs for different input methods
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
            ),
            padding=padding_all(16),
        )
        self._qr_tab = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.Icons.QR_CODE_SCANNER,
                        size=80,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE),
                    ),
                    ft.Text(
                        "Scan an otpauth QR code",
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                    ),
                    button(
                        "Scan with Camera",
                        icon=ft.Icons.PHOTO_CAMERA,
                        on_click=self._scan_camera,
                    ),
                    button(
                        "Select Image",
                        icon=ft.Icons.IMAGE,
                        on_click=self._pick_image,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
            padding=padding_all(32),
        )
        self._uri_tab = ft.Container(
            content=ft.Column(
                controls=[
                    self._uri_field,
                    button(
                        "Import from URI",
                        icon=ft.Icons.IMPORT_EXPORT,
                        on_click=self._import_uri,
                    ),
                ],
                spacing=12,
            ),
            padding=padding_all(16),
        )
        # --- Input-method switcher ------------------------------------------
        # flet 0.85's native Tabs (TabBar + TabBarView controller pattern) did
        # not switch views on tap in the packaged Android build, so we drive the
        # switch ourselves: tappable segments + a content container we swap
        # explicitly. Container.on_click is a reliable tap target on mobile.
        self._method_views = [self._manual_tab, self._qr_tab, self._uri_tab]
        self._method_content = ft.Container(content=self._manual_tab, expand=True)

        def _segment(idx: int, label: str, icon) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[ft.Icon(icon, size=18), ft.Text(label)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                on_click=lambda e, i=idx: self._select_method(i),
                padding=padding_symmetric(horizontal=8, vertical=10),
                border_radius=10,
                ink=True,
                expand=True,
            )

        self._segment_buttons = [
            _segment(0, "Manual", ft.Icons.EDIT),
            _segment(1, "Scan QR", ft.Icons.QR_CODE_SCANNER),
            _segment(2, "Paste URI", ft.Icons.CONTENT_PASTE),
        ]
        self._method_bar = ft.Container(
            content=ft.Row(controls=self._segment_buttons, spacing=4),
            padding=padding_symmetric(horizontal=12),
        )

        # Error text
        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=13,
            visible=False,
        )

        # Buttons
        self._save_btn = button(
            "Save Account",
            icon=ft.Icons.SAVE,
            on_click=self._save_manual,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        )

        # Save button lives inside the Manual view — only manual entry needs it;
        # the QR and URI views have their own action buttons.
        self._manual_tab.content.controls.append(
            ft.Container(content=self._save_btn, padding=padding_only(top=8))
        )

        # Apply initial segment selection styling (no page update yet — not mounted).
        self._apply_method(0)

        self.expand = True
        self.controls = [
            ft.Container(
                content=ft.Text(
                    "Add Account",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                padding=padding_only(left=16, top=16, bottom=8),
            ),
            self._method_bar,
            self._error_text,
            self._method_content,
        ]

    def _apply_method(self, index: int) -> None:
        """Set the visible input view and segment styling (no page update)."""
        self._method_content.content = self._method_views[index]
        for i, seg in enumerate(self._segment_buttons):
            seg.bgcolor = (
                ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY) if i == index else None
            )

    def _select_method(self, index: int) -> None:
        """Switch the visible input method (Manual / Scan QR / Paste URI)."""
        self._apply_method(index)
        self._clear_error()
        self.update()

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        self._error_text.value = message
        self._error_text.visible = True
        self.update()

    def _clear_error(self) -> None:
        """Clear the error message."""
        self._error_text.value = ""
        self._error_text.visible = False

    def _save_manual(self, e) -> None:
        """Save account from manual entry fields."""
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

        # Validate secret is valid Base32
        try:
            import base64
            # Add padding if needed
            padding = 8 - len(secret) % 8
            if padding != 8:
                secret += "=" * padding
            base64.b32decode(secret)
        except Exception:
            self._show_error("Invalid Base32 secret key")
            return

        # Remove padding for storage
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
        """Import account from a pasted otpauth:// URI."""
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
        """Open the live camera scanner (native extension) in a dialog."""
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
            title=ft.Text("Scan QR code"),
            content=ft.Container(width=300, height=300, content=scanner),
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
        """Close and discard the camera scanner dialog if open."""
        dialog = getattr(self, "_scan_dialog", None)
        if dialog is not None:
            dialog.open = False
            self._scan_dialog = None
            self.app_page.update()

    def _on_qr_detected(self, e) -> None:
        """Handle a decoded value from the live camera scanner."""
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
        """Open file picker to select a QR code image."""
        def _on_result(result: ft.FilePickerResultEvent):
            if result.files:
                try:
                    from src.core.qr import scan_qr_from_image
                    from pathlib import Path

                    image_path = Path(result.files[0].path)
                    uri = scan_qr_from_image(image_path)

                    if uri and uri.startswith("otpauth://"):
                        account = parse_otpauth_uri(uri)
                        self.vault.add_account(account)
                        if self._on_done:
                            self._on_done()
                    else:
                        self._show_error("No valid otpauth QR code found in image")
                except Exception as ex:
                    self._show_error(f"Failed to scan QR: {ex}")

        file_picker = ft.FilePicker(on_result=_on_result)
        self.app_page.overlay.append(file_picker)
        self.app_page.update()
        file_picker.pick_files(
            dialog_title="Select QR Code Image",
            file_type=ft.FilePickerFileType.IMAGE,
        )
