"""Tests for QR generation and image decoding (Pillow + pyzbar path).

QR *generation* is pure Python and always tested. QR *decoding* relies on the
native zbar library via pyzbar. zbar is bundled by Flet for Android builds, but
local desktop environments may lack a working zbar (notably, Homebrew's
zbar 0.23.93 segfaults on Apple Silicon). Because a segfault cannot be caught
in-process, decode tests are guarded by a subprocess probe and skipped when the
local zbar cannot decode.
"""

import base64
import subprocess
import sys

import pytest

from src.core.qr import (
    generate_qr_data_uri,
    generate_qr_file,
    scan_qr_from_bytes,
    scan_qr_from_image,
)

URI = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub"


def _png_bytes(uri: str) -> bytes:
    data_uri = generate_qr_data_uri(uri)
    assert data_uri.startswith("data:image/png;base64,")
    return base64.b64decode(data_uri.split(",", 1)[1])


def _zbar_decode_works() -> bool:
    """Probe, in a subprocess, whether the local zbar can decode without crashing."""
    probe = (
        "from PIL import Image; from pyzbar import pyzbar;"
        "import sys; sys.exit(0 if pyzbar.decode(Image.new('RGB',(16,16),'white'))==[] else 0)"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


_DECODE_OK = _zbar_decode_works()
requires_zbar = pytest.mark.skipif(
    not _DECODE_OK, reason="working native zbar not available in this environment"
)


def test_generate_data_uri_is_png():
    assert generate_qr_data_uri(URI).startswith("data:image/png;base64,")


def test_generate_file_writes_png(tmp_path):
    path = tmp_path / "code.png"
    generate_qr_file(URI, path)
    assert path.exists() and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@requires_zbar
def test_scan_from_bytes_roundtrip():
    assert scan_qr_from_bytes(_png_bytes(URI)) == URI


@requires_zbar
def test_scan_from_file_roundtrip(tmp_path):
    path = tmp_path / "code.png"
    generate_qr_file(URI, path)
    assert scan_qr_from_image(path) == URI


@requires_zbar
def test_scan_prefers_otpauth_payload():
    assert scan_qr_from_bytes(_png_bytes("hello-world")) == "hello-world"


@requires_zbar
def test_scan_from_bytes_invalid_image_returns_none():
    assert scan_qr_from_bytes(b"not-an-image") is None


def test_scan_from_missing_file_returns_none(tmp_path):
    # Missing file is handled before any zbar call, so this needs no zbar.
    assert scan_qr_from_image(tmp_path / "does-not-exist.png") is None
