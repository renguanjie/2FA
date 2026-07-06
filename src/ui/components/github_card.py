"""GitHub-specific card component for the GitHub integration page.

Design: elevated card with gradient left accent, status badge,
and modern layout consistent with OTP cards.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService
from src.ui.flet_compat import border_all, padding_all, padding_symmetric


class GitHubCard(ft.GestureDetector):
    """A card displaying a GitHub account with 2FA status and OAuth info."""

    def __init__(
        self,
        account: OTPAccount,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        two_factor_enabled: Optional[bool] = None,
        on_copy: Optional[Callable[[str], None]] = None,
        on_login: Optional[Callable[[OTPAccount], None]] = None,
    ):
        self.account = account
        self._on_copy = on_copy
        self._on_login = on_login

        github_color = "#24292E"

        # 2FA status badge
        if two_factor_enabled is True:
            status_badge = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color="#10B981"),
                        ft.Text(
                            "2FA Enabled",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color="#10B981",
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, "#10B981"),
                border_radius=12,
                padding=padding_symmetric(horizontal=8, vertical=4),
            )
        elif two_factor_enabled is False:
            status_badge = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING, size=14, color="#F59E0B"),
                        ft.Text(
                            "2FA Disabled",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color="#F59E0B",
                        ),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, "#F59E0B"),
                border_radius=12,
                padding=padding_symmetric(horizontal=8, vertical=4),
            )
        else:
            status_badge = ft.Container()

        # TOTP code
        code = OTPService.generate_for_account(account)
        mid = len(code) // 2
        code_display = ft.Text(
            f"{code[:mid]} {code[mid:]}",
            size=26,
            weight=ft.FontWeight.BOLD,
            font_family="monospace",
            color=github_color,
        )

        # Action buttons
        copy_btn = ft.Container(
            content=ft.Icon(ft.Icons.COPY, size=18, color=github_color),
            width=36,
            height=36,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.08, github_color),
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._handle_copy(),
            ink=True,
        )
        open_btn = ft.Container(
            content=ft.Icon(
                ft.Icons.OPEN_IN_BROWSER, size=18, color=github_color
            ),
            width=36,
            height=36,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.08, github_color),
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._handle_login(),
            ink=True,
        )

        # Left accent stripe
        accent_stripe = ft.Container(
            width=4,
            border_radius=ft.border_radius.only(
                top_left=14, bottom_left=14
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    github_color,
                    ft.Colors.with_opacity(0.3, github_color),
                ],
                tile_mode=ft.GradientTileMode.CLAMP,
            ),
        )

        card_body = ft.Container(
            content=ft.Row(
                controls=[
                    accent_stripe,
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.CircleAvatar(
                                            foreground_image_src=avatar_url,
                                            content=ft.Text(
                                                (username or account.name)[0].upper()
                                                if (username or account.name)
                                                else "G"
                                            ),
                                            radius=20,
                                        ),
                                        ft.Column(
                                            controls=[
                                                ft.Text(
                                                    username or account.name,
                                                    size=15,
                                                    weight=ft.FontWeight.W_700,
                                                ),
                                                ft.Text(
                                                    account.issuer,
                                                    size=12,
                                                    color=ft.Colors.with_opacity(
                                                        0.55,
                                                        ft.Colors.ON_SURFACE,
                                                    ),
                                                ),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                        status_badge,
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Container(height=8),
                                ft.Row(
                                    controls=[
                                        code_display,
                                        ft.Container(expand=True),
                                        copy_btn,
                                        ft.Container(width=6),
                                        open_btn,
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
            border=border_all(
                1, ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)
            ),
            shadow=[
                ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                    offset=ft.Offset(0, 4),
                ),
            ],
            ink=True,
        )

        super().__init__(content=card_body)

    def _handle_copy(self) -> None:
        code = OTPService.generate_for_account(self.account)
        if self._on_copy:
            self._on_copy(code)

    def _handle_login(self) -> None:
        if self._on_login:
            self._on_login(self.account)
