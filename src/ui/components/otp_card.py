"""OTP account card component.

Displays account info, current OTP code, and countdown timer.
Tap to copy code. Long press for options.

Design: elevated card with a brand-coloured left accent stripe,
issuer icon inside a tinted circular badge, and a smooth
countdown ring that shifts colour as time runs out.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService, OTPType
from src.ui.flet_compat import border_all, padding_all, padding_symmetric
from src.ui.theme import get_color_for_issuer, get_icon_for_issuer


class OTPCard(ft.GestureDetector):
    """A card displaying an OTP account with live code and countdown."""

    def __init__(
        self,
        account: OTPAccount,
        on_copy: Optional[Callable[[str], None]] = None,
        on_long_press: Optional[Callable[[OTPAccount], None]] = None,
    ):
        self.account = account
        self._on_copy = on_copy
        self._on_long_press = on_long_press

        issuer_color = get_color_for_issuer(account.issuer)

        # OTP code display
        self._code_text = ft.Text(
            "",
            size=30,
            weight=ft.FontWeight.BOLD,
            font_family="monospace",
            text_align=ft.TextAlign.CENTER,
            color=issuer_color,
        )

        # Countdown ring (only for TOTP)
        self._countdown_ring = ft.ProgressRing(
            value=1.0,
            width=38,
            height=38,
            stroke_width=3.5,
            color=issuer_color,
            bgcolor=ft.Colors.with_opacity(0.08, issuer_color),
        )

        # Issuer icon inside a tinted circular badge
        icon = get_icon_for_issuer(account.issuer)
        self._issuer_badge = ft.Container(
            content=ft.Icon(icon, size=18, color=issuer_color),
            bgcolor=ft.Colors.with_opacity(0.12, issuer_color),
            border_radius=10,
            width=36,
            height=36,
            alignment=ft.Alignment.CENTER,
        )

        self._issuer_row = ft.Row(
            controls=[
                self._issuer_badge,
                ft.Column(
                    controls=[
                        ft.Text(
                            account.issuer or "Unknown",
                            size=14,
                            weight=ft.FontWeight.W_700,
                        ),
                        ft.Container(
                            content=ft.Text(
                                "GitHub",
                                size=9,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=ft.Colors.BLACK,
                            border_radius=4,
                            padding=padding_symmetric(horizontal=5, vertical=1),
                            visible=account.is_github,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._name_text = ft.Text(
            account.name,
            size=13,
            color=ft.Colors.with_opacity(0.55, ft.Colors.ON_SURFACE),
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )

        # Left accent stripe (gradient bar)
        accent_stripe = ft.Container(
            width=4,
            border_radius=ft.BorderRadius(14, 0, 14, 0),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[issuer_color, ft.Colors.with_opacity(0.3, issuer_color)],
                tile_mode=ft.GradientTileMode.CLAMP,
            ),
        )

        # Build the card content
        card_body = ft.Container(
            content=ft.Row(
                controls=[
                    accent_stripe,
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self._issuer_row,
                                ft.Container(height=2),
                                self._name_text,
                                ft.Container(height=6),
                                ft.Row(
                                    controls=[
                                        self._code_text,
                                        ft.Container(expand=True),
                                        self._countdown_ring
                                        if account.otp_type == OTPType.TOTP
                                        else ft.Container(),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                            spacing=0,
                            tight=True,
                        ),
                        expand=True,
                        padding=padding_all(14),
                    ),
                ],
                spacing=0,
            ),
            border_radius=14,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
            border=border_all(1, ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)),
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                    offset=ft.Offset(0, 4),
                ),
            ],
            animate_opacity=ft.Animation(200),
            ink=True,
        )

        super().__init__(
            content=card_body,
            on_tap=self._handle_tap,
            on_long_press_start=self._handle_long_press,
        )

        # Initialize the code
        self._update_code()

    def _update_code(self) -> None:
        """Generate and display the current OTP code."""
        code = OTPService.generate_for_account(self.account)
        mid = len(code) // 2
        formatted = f"{code[:mid]} {code[mid:]}"
        self._code_text.value = formatted

    def _update_countdown(self) -> None:
        """Update the countdown ring for TOTP accounts."""
        if self.account.otp_type == OTPType.TOTP:
            remaining = OTPService.get_remaining_seconds(self.account.period)
            self._countdown_ring.value = remaining / self.account.period

            issuer_color = get_color_for_issuer(self.account.issuer)
            if remaining <= 5:
                self._countdown_ring.color = ft.Colors.RED
                self._code_text.color = ft.Colors.RED
            elif remaining <= 10:
                self._countdown_ring.color = ft.Colors.ORANGE
                self._code_text.color = ft.Colors.ORANGE
            else:
                self._countdown_ring.color = issuer_color
                self._code_text.color = issuer_color

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
