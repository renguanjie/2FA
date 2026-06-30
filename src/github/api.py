"""GitHub REST API wrapper for 2FA management.

Reference: https://docs.github.com/en/rest
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx



@dataclass
class GitHubUser:
    """GitHub user information."""

    login: str
    name: Optional[str]
    email: Optional[str]
    avatar_url: str
    two_factor_enabled: bool
    id: int


class GitHubAPIError(Exception):
    """GitHub API error."""


class GitHubAPI:
    """GitHub REST API client for 2FA-related operations.

    Usage:
        api = GitHubAPI()
        user = api.get_user("ghp_xxxx")
        print(f"{user.login} has 2FA: {user.two_factor_enabled}")
    """

    API_BASE = "https://api.github.com"

    def _headers(self, token: str) -> dict:
        """Build request headers with authorization."""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_user(self, token: str) -> GitHubUser:
        """Get authenticated user information.

        Args:
            token: GitHub OAuth access token.

        Returns:
            GitHubUser with user details and 2FA status.

        Raises:
            GitHubAPIError: If the API call fails.
        """
        with httpx.Client() as client:
            resp = client.get(
                f"{self.API_BASE}/user",
                headers=self._headers(token),
            )

        if resp.status_code != 200:
            raise GitHubAPIError(f"Failed to get user: {resp.status_code} {resp.text}")

        data = resp.json()

        return GitHubUser(
            login=data["login"],
            name=data.get("name"),
            email=data.get("email"),
            avatar_url=data.get("avatar_url", ""),
            two_factor_enabled=data.get("two_factor_authentication", False),
            id=data["id"],
        )

    def check_2fa_status(self, token: str) -> dict:
        """Check detailed 2FA status for the authenticated user.

        Args:
            token: GitHub OAuth access token.

        Returns:
            Dict with 2FA method details.
        """
        user = self.get_user(token)
        return {
            "login": user.login,
            "two_factor_enabled": user.two_factor_enabled,
            "has_totp": True if user.two_factor_enabled else None,  # Can't distinguish methods via API
        }

    def list_orgs(self, token: str) -> list[dict]:
        """List organizations the user belongs to.

        Args:
            token: GitHub OAuth access token.

        Returns:
            List of organization dicts.
        """
        with httpx.Client() as client:
            resp = client.get(
                f"{self.API_BASE}/user/orgs",
                headers=self._headers(token),
            )

        if resp.status_code != 200:
            raise GitHubAPIError(f"Failed to list orgs: {resp.status_code}")

        return resp.json()

    def get_user_emails(self, token: str) -> list[dict]:
        """Get user's email addresses.

        Args:
            token: GitHub OAuth access token.

        Returns:
            List of email dicts with 'email', 'primary', 'verified' fields.
        """
        with httpx.Client() as client:
            resp = client.get(
                f"{self.API_BASE}/user/emails",
                headers=self._headers(token),
            )

        if resp.status_code != 200:
            raise GitHubAPIError(f"Failed to get emails: {resp.status_code}")

        return resp.json()
