"""Modern Material Design 3 theme configuration for the 2FA app.

Uses a vibrant teal-to-indigo gradient palette with rich surface tints
for a lively, non-rigid look.
"""

from __future__ import annotations

import flet as ft


# ---------------------------------------------------------------------------
# Brand gradient palette (reused across screens / cards / buttons)
# ---------------------------------------------------------------------------

BRAND_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment.TOP_LEFT,
    end=ft.Alignment.BOTTOM_RIGHT,
    colors=[
        "#6366F1",  # indigo-500
        "#8B5CF6",  # violet-500
        "#06B6D4",  # cyan-500
    ],
    tile_mode=ft.GradientTileMode.CLAMP,
)

BRAND_GRADIENT_HORIZONTAL = ft.LinearGradient(
    begin=ft.Alignment.CENTER_LEFT,
    end=ft.Alignment.CENTER_RIGHT,
    colors=[
        "#6366F1",
        "#8B5CF6",
        "#06B6D4",
    ],
    tile_mode=ft.GradientTileMode.CLAMP,
)

ACCENT_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment.CENTER_LEFT,
    end=ft.Alignment.CENTER_RIGHT,
    colors=[
        "#F59E0B",  # amber-500
        "#EF4444",  # red-500
        "#EC4899",  # pink-500
    ],
    tile_mode=ft.GradientTileMode.CLAMP,
)

SUCCESS_GRADIENT = ft.LinearGradient(
    begin=ft.Alignment.CENTER_LEFT,
    end=ft.Alignment.CENTER_RIGHT,
    colors=["#10B981", "#34D399"],
    tile_mode=ft.GradientTileMode.CLAMP,
)

# Soft surface gradient for card / section backgrounds
SURFACE_GRADIENT_LIGHT = ft.LinearGradient(
    begin=ft.Alignment.TOP_CENTER,
    end=ft.Alignment.BOTTOM_CENTER,
    colors=[
        ft.Colors.with_opacity(0.02, ft.Colors.PRIMARY),
        ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY),
    ],
    tile_mode=ft.GradientTileMode.CLAMP,
)


def get_theme() -> ft.Theme:
    """Get the app's Material Design 3 theme with a vibrant teal/indigo seed."""
    return ft.Theme(
        color_scheme_seed=ft.Colors.TEAL,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


def get_dark_theme() -> ft.Theme:
    """Get the dark theme variant with richer surface tints."""
    return ft.Theme(
        color_scheme_seed=ft.Colors.TEAL,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            brightness=ft.Brightness.DARK,
        ),
    )


# ---------------------------------------------------------------------------
# Issuer-specific colour accents (used by OTP card / home page)
# ---------------------------------------------------------------------------

ISSUER_COLORS: dict[str, str] = {
    "github": "#6E40C9",
    "google": "#4285F4",
    "microsoft": "#00A4EF",
    "amazon": "#FF9900",
    "facebook": "#1877F2",
    "twitter": "#1DA1F2",
    "discord": "#5865F2",
    "steam": "#1B2838",
    "dropbox": "#0061FF",
    "aws": "#FF9900",
    "cloudflare": "#F38020",
    "bitbucket": "#0052CC",
    "gitlab": "#FC6D26",
    "apple": "#A2AAAD",
    "slack": "#4A154B",
    "notion": "#000000",
}


def get_color_for_issuer(issuer: str) -> str:
    """Return a brand hex colour for a known service issuer."""
    issuer_lower = issuer.lower()
    for key, color in ISSUER_COLORS.items():
        if key in issuer_lower:
            return color
    return "#6366F1"  # default indigo


# Icon mappings for common services
SERVICE_ICONS = {
    "github": ft.Icons.CODE,
    "google": ft.Icons.EMAIL,
    "microsoft": ft.Icons.WINDOW,
    "amazon": ft.Icons.SHOPPING_CART,
    "facebook": ft.Icons.FACEBOOK,
    "twitter": ft.Icons.ALTERNATE_EMAIL,
    "discord": ft.Icons.CHAT,
    "steam": ft.Icons.GAMES,
    "dropbox": ft.Icons.CLOUD,
    "aws": ft.Icons.CLOUD_QUEUE,
    "cloudflare": ft.Icons.DNS,
    "bitbucket": ft.Icons.CODE_OFF,
    "gitlab": ft.Icons.CODE_ROUNDED,
    "slack": ft.Icons.CHAT_BUBBLE,
    "notion": ft.Icons.NOTE,
}


def get_icon_for_issuer(issuer: str) -> str:
    """Get an appropriate icon for a service issuer."""
    issuer_lower = issuer.lower()
    for key, icon in SERVICE_ICONS.items():
        if key in issuer_lower:
            return icon
    return ft.Icons.KEY  # Default key icon
