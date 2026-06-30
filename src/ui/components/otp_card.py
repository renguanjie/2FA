"""OTP account card component.

Displays account info, current OTP code, and countdown timer.
Tap to copy code. Long press for options.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService, OTPType
from src.ui.flet_compat import border_all, padding_all, padding_symmetric
from src.ui.theme import get_icon_for_issuer


class OTPCard(ft.GestureDetector):
    """A card displaying an OTP account with live code and countdown.

    Features:
    - Shows issuer, account name, and current OTP code
    - Animated countdown ring for TOTP
    - Tap to copy code to clipboard
    - Visual distinction for GitHub accounts
    """

    def __init__(
        self,
        account: OTPAccount,
        on_copy: Optional[Callable[[str], None]] = None,
        on_long_press: Optional[Callable[[OTPAccount], None]] = None,
    ):
        self.account = account
        self._on_copy = on_copy
        self._on_long_press = on_long_press

        # OTP code display
        self._code_text = ft.Text(
            "",
            size=28,
            weight=ft.FontWeight.BOLD,
            font_family="monospace",
            text_align=ft.TextAlign.CENTER,
        )

        # Countdown ring (only for TOTP)
        self._countdown_ring = ft.ProgressRing(
            value=1.0,
            width=36,
            height=36,
            stroke_width=3,
            color=ft.Colors.BLUE,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
        )

        # Account info
        icon = get_icon_for_issuer(account.issuer)
        issuer_color = ft.Colors.BLUE if account.is_github else ft.Colors.PRIMARY

        self._issuer_row = ft.Row(
            controls=[
                ft.Icon(icon, size=20, color=issuer_color),
                ft.Text(
                    account.issuer or "Unknown",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=issuer_color,
                ),
                ft.Container(
                    content=ft.Text(
                        "GitHub",
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    bgcolor=ft.Colors.BLACK,
                    border_radius=4,
                    padding=padding_symmetric(horizontal=6, vertical=2),
                    visible=account.is_github,
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.START,
        )

        self._name_text = ft.Text(
            account.name,
            size=13,
            color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )

        # Build the card content
        card_content = ft.Container(
            content=ft.Column(
                controls=[
                    self._issuer_row,
                    self._name_text,
                    ft.Row(
                        controls=[
                            self._code_text,
                            ft.Container(expand=True),
                            self._countdown_ring if account.otp_type == OTPType.TOTP else ft.Container(),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            padding=padding_all(16),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE),
            border=border_all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)),
        )

        super().__init__(
            content=card_content,
            on_tap=self._handle_tap,
            on_long_press_start=self._handle_long_press,
        )

        # Initialize the code
        self._update_code()

    def _update_code(self) -> None:
        """Generate and display the current OTP code."""
        code = OTPService.generate_for_account(self.account)
        # Format code with space in the middle for readability
        mid = len(code) // 2
        formatted = f"{code[:mid]} {code[mid:]}"
        self._code_text.value = formatted

    def _update_countdown(self) -> None:
        """Update the countdown ring for TOTP accounts."""
        if self.account.otp_type == OTPType.TOTP:
            remaining = OTPService.get_remaining_seconds(self.account.period)
            self._countdown_ring.value = remaining / self.account.period

    def _handle_tap(self, e) -> None:
        """Handle tap - copy code to clipboard."""
        code = OTPService.generate_for_account(self.account)
        if self._on_copy:
            self._on_copy(code)

    def _handle_long_press(self, e) -> None:
        """Handle long press - show options."""
        if self._on_long_press:
            self._on_long_press(self.account)

    def refresh(self) -> None:
        """Refresh the OTP code and countdown. Call this periodically."""
        self._update_code()
        self._update_countdown()
