"""TOTP countdown timer component.

Design: circular progress ring with a smooth colour shift
from indigo to orange to red as time runs out.
"""

from __future__ import annotations

import flet as ft


class CountdownTimer(ft.Container):
    """A visual countdown timer for TOTP code validity."""

    def __init__(self, period: int = 30):
        self.period = period
        self._progress = ft.ProgressRing(
            value=1.0,
            width=48,
            height=48,
            stroke_width=4,
            color="#6366F1",
            bgcolor=ft.Colors.with_opacity(0.08, "#6366F1"),
        )
        self._time_text = ft.Text(
            str(self.period),
            size=14,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color="#6366F1",
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
        return self.content

    def update_time(self, remaining: int) -> None:
        self._progress.value = remaining / self.period
        self._time_text.value = str(remaining)

        if remaining <= 5:
            self._progress.color = ft.Colors.RED
            self._time_text.color = ft.Colors.RED
            self._progress.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.RED)
        elif remaining <= 10:
            self._progress.color = ft.Colors.ORANGE
            self._time_text.color = ft.Colors.ORANGE
            self._progress.bgcolor = ft.Colors.with_opacity(
                0.08, ft.Colors.ORANGE
            )
        else:
            self._progress.color = "#6366F1"
            self._time_text.color = "#6366F1"
            self._progress.bgcolor = ft.Colors.with_opacity(0.08, "#6366F1")

        self.update()
