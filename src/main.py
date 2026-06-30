"""2FA Authenticator - Main entry point.

A secure 2FA authenticator Android app with GitHub integration.
Built with Flet (Flutter-based) and Python.
"""

import flet as ft

from src.ui.app import TwoFAApp


def app_main(page: ft.Page) -> None:
    """Application entry point."""
    TwoFAApp(page)


def main(page: ft.Page | None = None) -> None:
    """Start the app, or initialize it when called by Flet with a page."""
    if page is None:
        # Flet 0.80 renamed app() to run(); prefer the new entry point and
        # fall back to app() on older Flet versions.
        launch = getattr(ft, "run", None) or ft.app
        launch(app_main)
    else:
        app_main(page)


if __name__ == "__main__":
    main()
