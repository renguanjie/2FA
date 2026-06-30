"""QR code scanning and generation for otpauth:// URIs.

Uses:
  - Pillow + pyzbar for decoding QR images (works on desktop and, via Flet's
    mobile binary package index, on Android too)
  - qrcode for generation

Live camera scanning on mobile is handled separately by the native
``flet_qr_scanner`` extension; these helpers cover decoding from an image file
(e.g. a screenshot picked from the gallery).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional

import qrcode


def generate_qr_data_uri(uri: str, size: int = 200) -> str:
    """Generate a QR code as a data URI for display in the UI.

    Args:
        uri: The otpauth:// URI to encode.
        size: QR code image size in pixels.

    Returns:
        Data URI string (data:image/png;base64,...).
    """
    import base64

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def generate_qr_file(uri: str, output_path: Path, size: int = 200) -> None:
    """Generate a QR code and save to a file.

    Args:
        uri: The otpauth:// URI to encode.
        output_path: Path to save the PNG file.
        size: QR code size.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(output_path))


def _decode_qr(image) -> Optional[str]:
    """Decode a QR code from a PIL image, preferring otpauth:// payloads.

    Args:
        image: A ``PIL.Image`` instance.

    Returns:
        The decoded string, or ``None`` if no QR code is found.
    """
    from pyzbar import pyzbar

    decoded = pyzbar.decode(image)

    # Prefer an otpauth:// payload when several codes are present.
    for obj in decoded:
        data = obj.data.decode("utf-8")
        if data.startswith("otpauth://"):
            return data

    if decoded:
        return decoded[0].data.decode("utf-8")

    return None


def scan_qr_from_image(image_path: Path) -> Optional[str]:
    """Scan a QR code from an image file.

    Args:
        image_path: Path to the image containing a QR code.

    Returns:
        Decoded string from the QR code, or None if no QR found.
    """
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow and pyzbar are required for QR scanning")

    try:
        with Image.open(image_path) as img:
            return _decode_qr(img)
    except FileNotFoundError:
        return None


def scan_qr_from_bytes(image_bytes: bytes) -> Optional[str]:
    """Scan a QR code from raw image bytes.

    Args:
        image_bytes: Raw image data (PNG/JPEG).

    Returns:
        Decoded string from the QR code, or None if no QR found.
    """
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        raise RuntimeError("Pillow and pyzbar are required for QR scanning")

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            return _decode_qr(img)
    except UnidentifiedImageError:
        return None
