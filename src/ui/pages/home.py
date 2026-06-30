"""Home page - Account list with live OTP codes."""

from __future__ import annotations

import asyncio
from typing import Callable, Optional

import flet as ft

from src.core.otp import OTPAccount, OTPService
from src.core.vault import Vault
from src.ui.components.otp_card import OTPCard
from src.ui.flet_compat import padding_all, padding_only, padding_symmetric
from src.utils.clipboard import copy_to_clipboard


class HomePage(ft.Column):
    """Home page displaying all OTP accounts with live codes.

    Features:
    - Search/filter accounts
    - Group by issuer
    - Auto-refresh codes every second
    - Tap to copy, long press for options
    """

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
            border_radius=24,
            content_padding=padding_symmetric(horizontal=16, vertical=12),
            on_change=self._on_search,
            dense=True,
        )

        # Account list
        self._account_list = ft.ListView(
            spacing=8,
            expand=True,
            auto_scroll=False,
        )

        # Empty state
        self._empty_state = ft.Column(
            controls=[
                ft.Icon(ft.Icons.KEY_OFF, size=64, color=ft.Colors.with_opacity(0.3, ft.Colors.ON_SURFACE)),
                ft.Text(
                    "No accounts yet",
                    size=18,
                    weight=ft.FontWeight.W_500,
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
            spacing=8,
            expand=True,
        )

        # FAB
        self._fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=lambda _: self._on_add() if self._on_add else None,
            bgcolor=ft.Colors.BLUE,
            foreground_color=ft.Colors.WHITE,
        )

        self.expand = True
        self.controls = [
            self._search_field,
            self._account_list,
        ]

    def did_mount(self):
        """Called when the page is mounted. Load accounts and start refresh."""
        self._load_accounts()
        self._start_refresh()

    def will_unmount(self):
        """Called when the page is unmounted. Stop refresh."""
        self._stop_refresh()

    def _load_accounts(self, filter_text: str = "") -> None:
        """Load accounts from vault and display them."""
        self._cards.clear()
        self._account_list.controls.clear()

        if not self.vault.is_unlocked:
            self._account_list.controls.append(self._empty_state)
            self.update()
            return

        accounts = self.vault.get_all_accounts()

        # Apply filter
        if filter_text:
            filter_lower = filter_text.lower()
            accounts = [
                a for a in accounts
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

        # Build cards
        for group_name, group_accounts in groups.items():
            # Group header
            self._account_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        group_name,
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE),
                    ),
                    padding=padding_only(left=8, top=8, bottom=4),
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
        """Handle search input change."""
        self._load_accounts(e.control.value)

    def _start_refresh(self) -> None:
        """Start periodic OTP code refresh."""
        async def _refresh_loop():
            while True:
                for card in self._cards.values():
                    card.refresh()
                    card.update()
                await asyncio.sleep(1)

        self._refresh_task = asyncio.create_task(_refresh_loop())

    def _stop_refresh(self) -> None:
        """Stop the refresh task."""
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

    def _show_account_options(self, account: OTPAccount) -> None:
        """Show bottom sheet with account options."""
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
                        ft.Text(
                            f"{account.issuer}: {account.name}",
                            size=16,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Divider(),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.EDIT),
                            title=ft.Text("Edit"),
                            on_click=_edit,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.COPY),
                            title=ft.Text("Copy current code"),
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
                            leading=ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED),
                            title=ft.Text("Delete", color=ft.Colors.RED),
                            on_click=_delete,
                        ),
                    ],
                    tight=True,
                ),
                padding=padding_all(16),
            ),
        )

        self.app_page.overlay.append(bottom_sheet)
        bottom_sheet.open = True
        self.app_page.update()

    def _confirm_delete(self, account: OTPAccount) -> None:
        """Show delete confirmation dialog."""
        def _do_delete(e):
            self.vault.delete_account(account.id)
            dialog.open = False
            self.app_page.update()
            self._load_accounts()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete Account"),
            content=ft.Text(
                f"Are you sure you want to delete {account.issuer}: {account.name}?\n\n"
                "This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dialog, "open", False) or self.app_page.update()),
                ft.TextButton("Delete", on_click=_do_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
        )
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()

    def refresh_accounts(self) -> None:
        """Public method to reload the account list."""
        self._load_accounts()
