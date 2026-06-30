from typing import Optional

import flet as ft
from flet.controls.control_event import ControlEventHandler

__all__ = ["FletQrScanner"]


@ft.control("FletQrScanner")
class FletQrScanner(ft.LayoutControl):
    """A live camera QR/barcode scanner backed by the native ``mobile_scanner``
    Flutter package (CameraX/ML Kit on Android, AVFoundation/Vision on iOS).

    The ``on_detect`` handler receives a :class:`ft.Event` whose ``data`` is the
    decoded string (e.g. an ``otpauth://`` URI).
    """

    facing: str = "back"
    """Camera to use: ``"back"`` (default) or ``"front"``."""

    torch: bool = False
    """Whether the torch/flashlight is enabled."""

    on_detect: Optional[ControlEventHandler["FletQrScanner"]] = None
    """Called when a code is decoded; ``event.data`` holds the decoded string."""
