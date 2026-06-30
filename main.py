"""Flet build entry point.

`flet build` / `flet run` package the directory containing this file and run it
as the app's main module. Keeping it at the repository root means the existing
``src`` package (and its absolute ``from src...`` imports) resolve unchanged
both on desktop and in the mobile bundle.

The console-script entry for desktop installs remains ``src.main:main``.
"""

import flet as ft


def main(page: ft.Page) -> None:
    # Import inside main so that an import-time failure (e.g. a missing native
    # dependency in the mobile bundle) is caught and shown on-screen instead of
    # leaving the app on a blank white page where the error is invisible.
    try:
        from src.ui.app import TwoFAApp

        TwoFAApp(page)
    except Exception:
        import traceback

        page.controls.clear()
        page.add(
            ft.Column(
                controls=[
                    ft.Text("Startup error", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        traceback.format_exc(),
                        selectable=True,
                        size=11,
                        font_family="monospace",
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )
        page.update()


ft.run(main)
