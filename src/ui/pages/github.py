"""GitHub integration page."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from src.core.vault import Vault
from src.github.api import GitHubAPI
from src.github.oauth import GitHubOAuth
from src.ui.components.github_card import GitHubCard
from src.ui.flet_compat import button, padding_all, padding_only, show_snack_bar
from src.utils.clipboard import copy_to_clipboard


class GitHubPage(ft.Column):
    """GitHub integration page.

    Features:
    - OAuth Device Flow login
    - GitHub account management
    - 2FA status display
    - Quick code copy
    """

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

        # Status display
        self._status_text = ft.Text(
            "",
            size=14,
            text_align=ft.TextAlign.CENTER,
        )

        # Login section
        self._login_section = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.CODE,
                    size=64,
                    color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE),
                ),
                ft.Text(
                    "Connect to GitHub",
                    size=20,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Link your GitHub account to manage 2FA\nand view your security status.",
                    size=14,
                    color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                    text_align=ft.TextAlign.CENTER,
                ),
                self._status_text,
                button(
                    "Connect GitHub",
                    icon=ft.Icons.LOGIN,
                    on_click=self._start_device_flow,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12),
                        bgcolor=ft.Colors.BLACK,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            expand=True,
        )

        # Device flow verification section (hidden until flow starts)
        self._device_code_section = ft.Column(
            controls=[
                ft.Text(
                    "Enter this code on GitHub:",
                    size=16,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(
                    content=ft.Text(
                        "",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        font_family="monospace",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE),
                    border_radius=12,
                    padding=padding_all(20),
                    alignment=ft.Alignment.CENTER,
                ),
                button(
                    "Open GitHub",
                    icon=ft.Icons.OPEN_IN_BROWSER,
                    on_click=lambda _: self.app_page.launch_url("https://github.com/login/device"),
                ),
                ft.ProgressRing(width=24, height=24),
                ft.Text(
                    "Waiting for authorization...",
                    size=14,
                    color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=16,
            visible=False,
        )

        # GitHub accounts list (hidden until connected)
        self._accounts_list = ft.ListView(
            spacing=12,
            expand=True,
        )
        self._connected_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.CircleAvatar(
                            content=ft.Text(""),
                            radius=20,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text("", size=16, weight=ft.FontWeight.W_600),
                                ft.Text("", size=13),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            "Disconnect",
                            on_click=self._disconnect,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Text(
                    "Your GitHub 2FA Accounts",
                    size=16,
                    weight=ft.FontWeight.W_600,
                ),
                self._accounts_list,
            ],
            visible=False,
            expand=True,
        )

        self.expand = True
        self.controls = [
            ft.Container(
                content=ft.Text(
                    "GitHub",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                padding=padding_only(left=16, top=16, bottom=8),
            ),
            self._login_section,
            self._device_code_section,
            self._connected_section,
        ]

    def did_mount(self):
        """Check if already connected to GitHub."""
        self._check_existing_connection()

    def _check_existing_connection(self) -> None:
        """Check if we have an existing GitHub connection."""
        if not self.vault.is_unlocked:
            return

        connection = self.vault.get_github_connection()
        if connection:
            self._show_connected(connection["token"])

    def _show_connected(self, token: str) -> None:
        """Show the connected state with user info."""
        try:
            user = self._api.get_user(token)

            self._login_section.visible = False
            self._device_code_section.visible = False
            self._connected_section.visible = True

            # Update user info
            row = self._connected_section.controls[0]
            row.controls[0].foreground_image_src = user.avatar_url
            row.controls[0].content = ft.Text(user.login[0].upper())
            row.controls[1].controls[0].value = user.login
            row.controls[1].controls[1].value = user.name or user.email or ""

            # Load GitHub accounts
            self._load_github_accounts(token)

            self.update()
        except Exception:
            pass

    def _load_github_accounts(self, token: str) -> None:
        """Load and display GitHub accounts."""
        self._accounts_list.controls.clear()

        accounts = self.vault.get_all_accounts()
        github_accounts = [a for a in accounts if a.is_github]

        if not github_accounts:
            self._accounts_list.controls.append(
                ft.Text(
                    "No GitHub 2FA accounts found.\nAdd a GitHub account from the Home page.",
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                )
            )
            return

        for acc in github_accounts:
            card = GitHubCard(
                account=acc,
                on_copy=lambda code: copy_to_clipboard(self.app_page, code),
                on_login=lambda a: self.app_page.launch_url("https://github.com/login"),
            )
            self._accounts_list.controls.append(card)

    async def _start_device_flow(self, e) -> None:
        """Start the GitHub OAuth Device Flow."""
        if not self._client_id:
            self._status_text.value = "GitHub Client ID not configured. Set it in Settings."
            self._status_text.color = ft.Colors.RED
            self.update()
            return

        self._oauth = GitHubOAuth(client_id=self._client_id)

        try:
            self._status_text.value = "Starting authorization..."
            self._status_text.color = ft.Colors.BLUE
            self.update()

            device = await asyncio.to_thread(self._oauth.device_flow_start)

            # Show device code
            self._login_section.visible = False
            self._device_code_section.visible = True
            self._device_code_section.controls[1].content.value = device.user_code
            self.update()

            # Start polling in background
            self._device_flow_task = asyncio.create_task(
                self._poll_for_token(device.device_code, device.interval)
            )

        except Exception as ex:
            self._status_text.value = f"Error: {ex}"
            self._status_text.color = ft.Colors.RED
            self.update()

    async def _poll_for_token(self, device_code: str, interval: int) -> None:
        """Poll GitHub for the OAuth token."""
        try:
            token_resp = await asyncio.to_thread(
                self._oauth.device_flow_poll,
                device_code,
                interval,
            )

            user = await asyncio.to_thread(self._api.get_user, token_resp.access_token)
            self.vault.save_github_connection(user.login, token_resp.access_token)
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
        """Disconnect from GitHub."""
        if self.vault.is_unlocked:
            self.vault.clear_github_connection()
        self._connected_section.visible = False
        self._login_section.visible = True
        self._status_text.value = ""
        self.update()
