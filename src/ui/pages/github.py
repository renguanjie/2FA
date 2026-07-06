"""GitHub integration page.

Design: gradient header, card-based login / device-code / connected
sections with colourful icon badges and pill buttons.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from src.core.vault import Vault
from src.github.api import GitHubAPI
from src.github.oauth import GitHubOAuth
from src.ui.components.github_card import GitHubCard
from src.ui.flet_compat import (
    border_all,
    button,
    padding_all,
    show_snack_bar,
)
from src.ui.theme import BRAND_GRADIENT
from src.utils.clipboard import copy_to_clipboard


class GitHubPage(ft.Column):
    """GitHub integration page."""

    def __init__(
        self,
        vault: Vault,
        page: ft.Page,
        client_id: str = "",
    ):
        super().__init__()
        self.vault = vault
        self.app_page = page
        self._client_id = client_id
        self._oauth: Optional[GitHubOAuth] = None
        self._api = GitHubAPI()
        self._device_flow_task: Optional[asyncio.Task] = None

        self._status_text = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

        # -- Login section ------------------------------------------------
        self._login_section = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(ft.Icons.CODE, size=40, color=ft.Colors.WHITE),
                    width=80,
                    height=80,
                    border_radius=24,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_LEFT,
                        end=ft.Alignment.BOTTOM_RIGHT,
                        colors=["#24292E", "#586069"],
                    ),
                    alignment=ft.Alignment.CENTER,
                    shadow=[
                        ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=16,
                            color=ft.Colors.with_opacity(0.3, "#24292E"),
                            offset=ft.Offset(0, 6),
                        ),
                    ],
                ),
                ft.Container(height=8),
                ft.Text(
                    "Connect to GitHub",
                    size=20,
                    weight=ft.FontWeight.W_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Link your GitHub account to manage 2FA\nand view your security status.",
                    size=14,
                    color=ft.Colors.with_opacity(0.55, ft.Colors.ON_SURFACE),
                    text_align=ft.TextAlign.CENTER,
                ),
                self._status_text,
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.LOGIN, size=18, color=ft.Colors.WHITE),
                            ft.Text(
                                "Connect GitHub",
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.CENTER_LEFT,
                        end=ft.Alignment.CENTER_RIGHT,
                        colors=["#24292E", "#586069"],
                    ),
                    border_radius=14,
                    padding=padding_all(14),
                    ink=True,
                    on_click=self._start_device_flow,
                    shadow=[
                        ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=12,
                            color=ft.Colors.with_opacity(0.25, "#24292E"),
                            offset=ft.Offset(0, 4),
                        ),
                    ],
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # -- Device code section ------------------------------------------
        self._device_code_text = ft.Text(
            "",
            size=32,
            weight=ft.FontWeight.BOLD,
            font_family="monospace",
            text_align=ft.TextAlign.CENTER,
            color="#6366F1",
        )
        self._device_code_section = ft.Column(
            controls=[
                ft.Text(
                    "Enter this code on GitHub:",
                    size=16,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Container(
                    content=self._device_code_text,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY),
                    border_radius=16,
                    padding=padding_all(20),
                    alignment=ft.Alignment.CENTER,
                    border=border_all(1, ft.Colors.with_opacity(0.12, "#6366F1")),
                ),
                button(
                    "Open GitHub",
                    icon=ft.Icons.OPEN_IN_BROWSER,
                    on_click=lambda _: self.app_page.launch_url(
                        "https://github.com/login/device"
                    ),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                ),
                ft.ProgressRing(width=24, height=24, color="#6366F1"),
                ft.Text(
                    "Waiting for authorization...",
                    size=14,
                    color=ft.Colors.with_opacity(0.55, ft.Colors.ON_SURFACE),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            visible=False,
        )

        # -- Connected section --------------------------------------------
        self._accounts_list = ft.ListView(spacing=12, expand=True)
        self._connected_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.CircleAvatar(content=ft.Text(""), radius=22),
                        ft.Column(
                            controls=[
                                ft.Text("", size=16, weight=ft.FontWeight.W_700),
                                ft.Text(
                                    "",
                                    size=13,
                                    color=ft.Colors.with_opacity(
                                        0.55, ft.Colors.ON_SURFACE
                                    ),
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            "Disconnect",
                            on_click=self._disconnect,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                color=ft.Colors.RED,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=4),
                ft.Container(
                    height=1,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
                ),
                ft.Text(
                    "Your GitHub 2FA Accounts",
                    size=16,
                    weight=ft.FontWeight.W_700,
                ),
                self._accounts_list,
            ],
            visible=False,
            expand=True,
        )

        self.expand = True
        self.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(
                                    "GitHub",
                                    size=22,
                                    weight=ft.FontWeight.W_800,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "Security integration",
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
                                ft.Icons.CODE, size=22, color=ft.Colors.WHITE
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
            self._login_section,
            self._device_code_section,
            self._connected_section,
        ]

    def did_mount(self):
        self._check_existing_connection()

    def _check_existing_connection(self) -> None:
        if not self.vault.is_unlocked:
            return
        connection = self.vault.get_github_connection()
        if connection:
            self._show_connected(connection["token"])

    def _show_connected(self, token: str) -> None:
        try:
            user = self._api.get_user(token)
            self._login_section.visible = False
            self._device_code_section.visible = False
            self._connected_section.visible = True

            row = self._connected_section.controls[0]
            row.controls[0].foreground_image_src = user.avatar_url
            row.controls[0].content = ft.Text(user.login[0].upper())
            row.controls[1].controls[0].value = user.login
            row.controls[1].controls[1].value = user.name or user.email or ""

            self._load_github_accounts(token)
            self.update()
        except Exception:
            pass

    def _load_github_accounts(self, token: str) -> None:
        self._accounts_list.controls.clear()
        accounts = self.vault.get_all_accounts()
        github_accounts = [a for a in accounts if a.is_github]

        if not github_accounts:
            self._accounts_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.INFO_OUTLINE,
                                size=40,
                                color=ft.Colors.with_opacity(
                                    0.3, ft.Colors.ON_SURFACE
                                ),
                            ),
                            ft.Text(
                                "No GitHub 2FA accounts found.\nAdd one from the Home page.",
                                text_align=ft.TextAlign.CENTER,
                                size=13,
                                color=ft.Colors.with_opacity(
                                    0.5, ft.Colors.ON_SURFACE
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=padding_all(24),
                    alignment=ft.Alignment.CENTER,
                )
            )
            return

        for acc in github_accounts:
            card = GitHubCard(
                account=acc,
                on_copy=lambda code: copy_to_clipboard(self.app_page, code),
                on_login=lambda a: self.app_page.launch_url(
                    "https://github.com/login"
                ),
            )
            self._accounts_list.controls.append(card)

    async def _start_device_flow(self, e) -> None:
        if not self._client_id:
            self._status_text.value = (
                "GitHub Client ID not configured. Set it in Settings."
            )
            self._status_text.color = ft.Colors.RED
            self.update()
            return

        self._oauth = GitHubOAuth(client_id=self._client_id)
        try:
            self._status_text.value = "Starting authorization..."
            self._status_text.color = "#6366F1"
            self.update()

            device = await asyncio.to_thread(self._oauth.device_flow_start)

            self._login_section.visible = False
            self._device_code_section.visible = True
            self._device_code_text.value = device.user_code
            self.update()

            self._device_flow_task = asyncio.create_task(
                self._poll_for_token(device.device_code, device.interval)
            )
        except Exception as ex:
            self._status_text.value = f"Error: {ex}"
            self._status_text.color = ft.Colors.RED
            self.update()

    async def _poll_for_token(
        self, device_code: str, interval: int
    ) -> None:
        try:
            token_resp = await asyncio.to_thread(
                self._oauth.device_flow_poll, device_code, interval
            )
            user = await asyncio.to_thread(
                self._api.get_user, token_resp.access_token
            )
            self.vault.save_github_connection(
                user.login, token_resp.access_token
            )
            self._device_code_section.visible = False
            self._show_connected(token_resp.access_token)

            show_snack_bar(
                self.app_page,
                ft.SnackBar(
                    content=ft.Text("Successfully connected to GitHub!"),
                    bgcolor=ft.Colors.GREEN,
                ),
            )
        except Exception as ex:
            self._device_code_section.visible = False
            self._login_section.visible = True
            self._status_text.value = f"Authorization failed: {ex}"
            self._status_text.color = ft.Colors.RED
            self.update()

    def _disconnect(self, e) -> None:
        if self.vault.is_unlocked:
            self.vault.clear_github_connection()
        self._connected_section.visible = False
        self._login_section.visible = True
        self._status_text.value = ""
        self.update()
