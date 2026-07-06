"""Home page - Account list with live OTP codes.

Design: a gradient header bar with app title + search,
a lively empty-state illustration, and colour-coded group headers.
"""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService
from src.core.vault import Vault
from src.ui.components.otp_card import OTPCard
from src.ui.flet_compat import padding_all, padding_only, padding_symmetric
from src.ui.theme import BRAND_GRADIENT, get_color_for_issuer
from src.utils.clipboard import copy_to_clipboard


class HomePage(ft.Column):
    """Home page displaying all OTP accounts with live codes."""

    def __init__(
        self,
        vault: Vault,
        page: ft.Page,
        on_add: Optional[Callable] = None,
    ):
        super().__init__()
        self.vault = vault
        self.app_page = page
        self._on_add = on_add
        self._cards: dict[str, OTPCard] = {}
        self._refresh_task: Optional[asyncio.Task] = None

        # Search bar
        self._search_field = ft.TextField(
            hint_text="Search accounts...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=14,
            content_padding=padding_symmetric(horizontal=16, vertical=12),
            on_change=self._on_search,
            dense=True,
            filled=True,
            fill_color=ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY),
            focused_border_color="#6366F1",
            border_color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
        )

        # Account list
        self._account_list = ft.ListView(
            spacing=10,
            expand=True,
            auto_scroll=False,
        )

        # Empty state — lively illustration
        self._empty_state = ft.Column(
            controls=[
                ft.Stack(
                    controls=[
                        ft.Container(
                            width=80,
                            height=80,
                            border_radius=40,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[
                                    ft.Colors.with_opacity(0.2, "#6366F1"),
                                    ft.Colors.with_opacity(0.05, "#6366F1"),
                                ],
                            ),
                        ),
                        ft.Container(
                            width=60,
                            height=60,
                            border_radius=30,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[
                                    ft.Colors.with_opacity(0.25, "#06B6D4"),
                                    ft.Colors.with_opacity(0.05, "#06B6D4"),
                                ],
                            ),
                            offset=ft.Offset(0.5, 0.4),
                        ),
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.KEY,
                                size=32,
                                color=ft.Colors.with_opacity(0.5, "#6366F1"),
                            ),
                            alignment=ft.Alignment.CENTER,
                            width=80,
                            height=80,
                        ),
                    ],
                    width=120,
                    height=100,
                ),
                ft.Text(
                    "No accounts yet",
                    size=18,
                    weight=ft.FontWeight.W_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Tap + to add your first 2FA account",
                    size=14,
                    color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        )

        self.expand = True
        self.controls = [
            # Gradient header
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "2FA Authenticator",
                                            size=20,
                                            weight=ft.FontWeight.W_800,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Text(
                                            "Your secure vault",
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
                                        ft.Icons.SHIELD,
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
                            alignment=ft.MainAxisAlignment.START,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=12),
                        self._search_field,
                    ],
                    spacing=0,
                ),
                padding=ft.Padding(16, 16, 16, 16),
                gradient=BRAND_GRADIENT,
                border_radius=ft.BorderRadius(0, 0, 20, 20),
            ),
            self._account_list,
        ]

    def did_mount(self):
        self._load_accounts()
        self._start_refresh()

    def will_unmount(self):
        self._stop_refresh()

    def _load_accounts(self, filter_text: str = "") -> None:
        self._cards.clear()
        self._account_list.controls.clear()

        if not self.vault.is_unlocked:
            self._account_list.controls.append(self._empty_state)
            self.update()
            return

        accounts = self.vault.get_all_accounts()

        if filter_text:
            filter_lower = filter_text.lower()
            accounts = [
                a
                for a in accounts
                if filter_lower in a.issuer.lower()
                or filter_lower in a.name.lower()
                or filter_lower in (a.notes or "").lower()
            ]

        if not accounts:
            self._account_list.controls.append(self._empty_state)
            self.update()
            return

        # Group by issuer
        groups: dict[str, list[OTPAccount]] = {}
        for acc in accounts:
            key = acc.group or acc.issuer or "Other"
            groups.setdefault(key, []).append(acc)

        for group_name, group_accounts in groups.items():
            group_color = get_color_for_issuer(group_name)
            self._account_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=8,
                                height=8,
                                border_radius=4,
                                bgcolor=group_color,
                            ),
                            ft.Text(
                                group_name,
                                size=12,
                                weight=ft.FontWeight.W_700,
                                color=group_color,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    str(len(group_accounts)),
                                    size=10,
                                    weight=ft.FontWeight.BOLD,
                                    color=group_color,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.1, group_color),
                                border_radius=8,
                                padding=padding_symmetric(
                                    horizontal=6, vertical=2
                                ),
                            ),
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=padding_only(left=12, top=10, bottom=4),
                )
            )

            for acc in group_accounts:
                card = OTPCard(
                    account=acc,
                    on_copy=lambda code: copy_to_clipboard(self.app_page, code),
                    on_long_press=self._show_account_options,
                )
                self._cards[acc.id] = card
                self._account_list.controls.append(card)

        self.update()

    def _on_search(self, e) -> None:
        self._load_accounts(e.control.value)

    def _start_refresh(self) -> None:
        async def _refresh_loop():
            while True:
                for card in self._cards.values():
                    card.refresh()
                    card.update()
                await asyncio.sleep(1)

        self._refresh_task = asyncio.create_task(_refresh_loop())

    def _stop_refresh(self) -> None:
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    def _show_account_options(self, account: OTPAccount) -> None:
        issuer_color = get_color_for_issuer(account.issuer)

        def _close(e):
            bottom_sheet.open = False
            self.app_page.update()

        def _delete(e):
            bottom_sheet.open = False
            self.app_page.update()
            self._confirm_delete(account)

        def _edit(e):
            bottom_sheet.open = False
            self.app_page.update()

        bottom_sheet = ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        account.issuer[0].upper()
                                        if account.issuer
                                        else "?",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                    ),
                                    width=44,
                                    height=44,
                                    border_radius=14,
                                    gradient=ft.LinearGradient(
                                        begin=ft.Alignment.TOP_LEFT,
                                        end=ft.Alignment.BOTTOM_RIGHT,
                                        colors=[
                                            issuer_color,
                                            ft.Colors.with_opacity(
                                                0.6, issuer_color
                                            ),
                                        ],
                                    ),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"{account.issuer}",
                                            size=16,
                                            weight=ft.FontWeight.W_700,
                                        ),
                                        ft.Text(
                                            account.name,
                                            size=13,
                                            color=ft.Colors.with_opacity(
                                                0.55, ft.Colors.ON_SURFACE
                                            ),
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=8),
                        ft.Container(
                            height=1,
                            bgcolor=ft.Colors.with_opacity(
                                0.08, ft.Colors.ON_SURFACE
                            ),
                        ),
                        ft.Container(height=4),
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Icon(
                                    ft.Icons.EDIT, color=issuer_color
                                ),
                                width=36,
                                height=36,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(
                                    0.1, issuer_color
                                ),
                                alignment=ft.Alignment.CENTER,
                            ),
                            title=ft.Text("Edit", weight=ft.FontWeight.W_600),
                            on_click=_edit,
                        ),
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Icon(ft.Icons.COPY, color="#10B981"),
                                width=36,
                                height=36,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(0.1, "#10B981"),
                                alignment=ft.Alignment.CENTER,
                            ),
                            title=ft.Text(
                                "Copy current code",
                                weight=ft.FontWeight.W_600,
                            ),
                            on_click=lambda _: (
                                copy_to_clipboard(
                                    self.app_page,
                                    OTPService.generate_for_account(account),
                                ),
                                setattr(bottom_sheet, "open", False),
                                self.app_page.update(),
                            ),
                        ),
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.Icon(
                                    ft.Icons.DELETE, color=ft.Colors.RED
                                ),
                                width=36,
                                height=36,
                                border_radius=10,
                                bgcolor=ft.Colors.with_opacity(
                                    0.1, ft.Colors.RED
                                ),
                                alignment=ft.Alignment.CENTER,
                            ),
                            title=ft.Text(
                                "Delete",
                                color=ft.Colors.RED,
                                weight=ft.FontWeight.W_600,
                            ),
                            on_click=_delete,
                        ),
                        ft.Container(height=8),
                    ],
                    tight=True,
                ),
                padding=padding_all(20),
            ),
        )

        self.app_page.overlay.append(bottom_sheet)
        bottom_sheet.open = True
        self.app_page.update()

    def _confirm_delete(self, account: OTPAccount) -> None:
        def _do_delete(e):
            self.vault.delete_account(account.id)
            dialog.open = False
            self.app_page.update()
            self._load_accounts()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Account", weight=ft.FontWeight.W_700),
            content=ft.Text(
                f"Are you sure you want to delete {account.issuer}: {account.name}?\n\n"
                "This action cannot be undone."
            ),
            shape=ft.RoundedRectangleBorder(radius=16),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: setattr(dialog, "open", False)
                    or self.app_page.update(),
                ),
                ft.TextButton(
                    "Delete",
                    on_click=_do_delete,
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                ),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def refresh_accounts(self) -> None:
        self._load_accounts()
