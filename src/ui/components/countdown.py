"""TOTP countdown timer component."""

from __future__ import annotations

import flet as ft


class CountdownTimer(ft.Container):
    """A visual countdown timer for TOTP code validity.

    Displays remaining seconds and a circular progress indicator.
    """

    def __init__(self, period: int = 30):
        self.period = period
        self._progress = ft.ProgressRing(
            value=1.0,
            width=48,
            height=48,
            stroke_width=4,
            color=ft.Colors.BLUE,
        )
        self._time_text = ft.Text(
            str(self.period),
            size=14,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        super().__init__(
            content=ft.Stack(
                controls=[
                    self._progress,
                    ft.Container(
                        content=self._time_text,
                        alignment=ft.Alignment.CENTER,
                        width=48,
                        height=48,
                    ),
                ],
                width=48,
                height=48,
            ),
            width=48,
            height=48,
        )

    def build(self) -> ft.Control:
        """Return the underlying control for older call sites."""
        return self.content

    def update_time(self, remaining: int) -> None:
        """Update the countdown display.

        Args:
            remaining: Seconds remaining in the current period.
        """
        self._progress.value = remaining / self.period
        self._time_text.value = str(remaining)

        # Change color when time is running out
        if remaining <= 5:
            self._progress.color = ft.Colors.RED
        elif remaining <= 10:
            self._progress.color = ft.Colors.ORANGE
        else:
            self._progress.color = ft.Colors.BLUE

        self.update()
