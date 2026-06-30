"""Material Design 3 theme configuration for the 2FA app."""

import flet as ft


def get_theme() -> ft.Theme:
    """Get the app's Material Design 3 theme.

    Uses a blue-based color scheme suitable for a security-focused app.
    """
    return ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


def get_dark_theme() -> ft.Theme:
    """Get the dark theme variant."""
    return ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True,
        visual_density=ft.VisualDensity.COMFORTABLE,
        color_scheme=ft.ColorScheme(
            brightness=ft.Brightness.DARK,
        ),
    )


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
}


def get_icon_for_issuer(issuer: str) -> ft.Icons:
    """Get an appropriate icon for a service issuer.

    Args:
        issuer: The service name (e.g. "GitHub", "Google").

    Returns:
        Material icon constant.
    """
    issuer_lower = issuer.lower()
    for key, icon in SERVICE_ICONS.items():
        if key in issuer_lower:
            return icon
    return ft.Icons.KEY  # Default key icon
