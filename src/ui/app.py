"""Main Flet application with page routing.

Design: brand-gradient FAB, tinted navigation bar indicator,
smooth AnimatedSwitcher transitions between pages.
"""

from __future__ import annotations

import asyncio
import time

import flet as ft

from src.config import Config
from src.core.vault import Vault
from src.storage.database import init_db
from src.ui.pages.add_account import AddAccountPage
from src.ui.pages.backup import BackupPage
from src.ui.pages.github import GitHubPage
from src.ui.pages.home import HomePage
from src.ui.pages.lock import LockPage
from src.ui.pages.settings import SettingsPage
from src.ui.flet_compat import set_window_size
from src.ui.theme import get_theme


class TwoFAApp:
    """Main application class managing navigation and state.

    Flow:
    1. App starts -> Lock screen
    2. User unlocks -> Home page with OTP accounts
    3. Bottom navigation: Home | GitHub | Settings
    """

    def __init__(self, page: ft.Page):
        self.page = page
        Config.load_settings()
        self._vault = Vault(Config.get_db_path())

        init_db(Config.get_db_path())

        page.title = Config.APP_NAME
        page.theme = get_theme()
        page.theme_mode = ft.ThemeMode.SYSTEM
        set_window_size(page, 400, 800)
        page.padding = 0

        # Navigation
        self._current_index = 0
        self._rail = None
        self._last_activity = time.monotonic()
        self._auto_lock_task: asyncio.Task | None = None
        self._previous_keyboard_handler = page.on_keyboard_event
        page.on_keyboard_event = self._on_keyboard_event

        # Pages (lazy init)
        self._home_page: HomePage | None = None
        self._github_page: GitHubPage | None = None
        self._settings_page: SettingsPage | None = None
        self._backup_page: BackupPage | None = None
        self._add_page: AddAccountPage | None = None

        # Content area with fade transition — expand=True is required so
        # child pages (Columns with expand) receive bounded height from
        # the parent; without it ListViews can't scroll.
        self._content = ft.AnimatedSwitcher(
            content=ft.Container(),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=250,
            expand=True,
        )

        # Bottom navigation bar with tinted indicator
        self._nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=self._on_nav_change,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CODE_OUTLINED,
                    selected_icon=ft.Icons.CODE,
                    label="GitHub",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                    label="Settings",
                ),
            ],
            indicator_color="#6366F1",
            indicator_shape=ft.RoundedRectangleBorder(radius=16),
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
            elevation=0,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            visible=False,
        )

        # FAB - indigo rounded with glow
        self._fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=self._show_add_page,
            bgcolor="#6366F1",
            foreground_color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=16),
            elevation=6,
        )

        self._show_lock()

    def _show_lock(self) -> None:
        self._stop_auto_lock()
        self._nav_bar.visible = False
        self.page.floating_action_button = None

        lock_page = LockPage(
            vault=self._vault,
            page=self.page,
            on_unlock=self._on_vault_unlocked,
        )

        self._content.content = lock_page
        self.page.controls.clear()
        self.page.add(
            ft.SafeArea(
                content=ft.Column(
                    controls=[
                        self._content,
                        self._nav_bar,
                    ],
                    expand=True,
                ),
                expand=True,
            ),
        )
        self.page.update()

    def _on_vault_unlocked(self) -> None:
        self._nav_bar.visible = True
        self.page.floating_action_button = self._fab
        self._record_activity()
        self._start_auto_lock()
        self._show_home()

    def _show_home(self) -> None:
        self._current_index = 0
        self._record_activity()
        self._nav_bar.selected_index = 0
        self.page.floating_action_button = self._fab

        self._home_page = HomePage(
            vault=self._vault,
            page=self.page,
            on_add=self._show_add_page,
        )

        self._content.content = self._home_page
        self.page.update()

    def _show_github(self) -> None:
        self._current_index = 1
        self._record_activity()
        self.page.floating_action_button = None

        self._github_page = GitHubPage(
            vault=self._vault,
            page=self.page,
            client_id=Config.GITHUB_CLIENT_ID,
        )

        self._content.content = self._github_page
        self.page.update()

    def _show_settings(self) -> None:
        self._current_index = 2
        self._record_activity()
        self.page.floating_action_button = None

        self._settings_page = SettingsPage(
            vault=self._vault,
            page=self.page,
            on_backup=self._show_backup,
            on_restore=self._show_backup,
        )

        self._content.content = self._settings_page
        self.page.update()

    def _show_backup(self) -> None:
        self._record_activity()
        self._backup_page = BackupPage(
            vault=self._vault,
            page=self.page,
        )

        self._content.content = self._backup_page
        self.page.update()

    def _show_add_page(self, e=None) -> None:
        self._record_activity()
        self.page.floating_action_button = None

        def _on_done():
            self._show_home()
            if self._home_page:
                self._home_page.refresh_accounts()

        self._add_page = AddAccountPage(
            vault=self._vault,
            page=self.page,
            on_done=_on_done,
        )

        self._content.content = self._add_page
        self.page.update()

    def _on_nav_change(self, e) -> None:
        index = e.control.selected_index
        if index == 0:
            self._show_home()
        elif index == 1:
            self._show_github()
        elif index == 2:
            self._show_settings()

    def _record_activity(self) -> None:
        self._last_activity = time.monotonic()

    def _on_keyboard_event(self, e) -> None:
        self._record_activity()
        if self._previous_keyboard_handler:
            self._previous_keyboard_handler(e)

    def _start_auto_lock(self) -> None:
        self._stop_auto_lock()
        if Config.AUTO_LOCK_SECONDS <= 0:
            return

        async def _auto_lock_loop():
            while self._vault.is_unlocked:
                await asyncio.sleep(1)
                if Config.AUTO_LOCK_SECONDS <= 0:
                    continue
                idle_seconds = time.monotonic() - self._last_activity
                if idle_seconds >= Config.AUTO_LOCK_SECONDS:
                    self._vault.lock()
                    self._show_lock()
                    return

        self._auto_lock_task = asyncio.create_task(_auto_lock_loop())

    def _stop_auto_lock(self) -> None:
        if self._auto_lock_task:
            self._auto_lock_task.cancel()
            self._auto_lock_task = None
