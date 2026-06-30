"""GitHub-specific card component for the GitHub integration page."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService
from src.ui.flet_compat import padding_all, padding_symmetric


class GitHubCard(ft.Card):
    """A card displaying a GitHub account with 2FA status and OAuth info.

    Shows:
    - GitHub avatar and username
    - Current TOTP code with countdown
    - 2FA enabled/disabled status badge
    - OAuth connection status
    """

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

        # Build GitHub-specific UI
        avatar = ft.CircleAvatar(
            foreground_image_src=avatar_url,
            content=ft.Text(account.name[0].upper() if account.name else "G"),
            radius=24,
        )

        # 2FA status badge
        if two_factor_enabled is True:
            status_badge = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=ft.Colors.GREEN),
                        ft.Text("2FA Enabled", size=12, color=ft.Colors.GREEN),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                border_radius=12,
                padding=padding_symmetric(horizontal=8, vertical=4),
            )
        elif two_factor_enabled is False:
            status_badge = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.WARNING, size=14, color=ft.Colors.ORANGE),
                        ft.Text("2FA Disabled", size=12, color=ft.Colors.ORANGE),
                    ],
                    spacing=4,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ORANGE),
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
            size=24,
            weight=ft.FontWeight.BOLD,
            font_family="monospace",
        )

        # Buttons
        copy_btn = ft.IconButton(
            icon=ft.Icons.COPY,
            tooltip="Copy code",
            on_click=lambda _: self._handle_copy(),
        )

        open_btn = ft.IconButton(
            icon=ft.Icons.OPEN_IN_BROWSER,
            tooltip="Open GitHub",
            on_click=lambda _: self._handle_login(),
        )

        super().__init__(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                avatar,
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            username or account.name,
                                            size=16,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            account.issuer,
                                            size=13,
                                            color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
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
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                code_display,
                                ft.Container(expand=True),
                                copy_btn,
                                open_btn,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=12,
                ),
                padding=padding_all(16),
            ),
            elevation=2,
        )

    def _handle_copy(self) -> None:
        code = OTPService.generate_for_account(self.account)
        if self._on_copy:
            self._on_copy(code)

    def _handle_login(self) -> None:
        if self._on_login:
            self._on_login(self.account)
