"""GitHub OAuth implementation.

Supports two flows:
1. Authorization Code Flow (for web/desktop)
2. Device Flow (for mobile devices - primary method)

Reference: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class DeviceCodeResponse:
    """Response from GitHub Device Flow initiation."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int  # Minimum polling interval in seconds


@dataclass
class TokenResponse:
    """GitHub OAuth token response."""

    access_token: str
    token_type: str
    scope: str


class GitHubOAuthError(Exception):
    """GitHub OAuth error."""


class GitHubOAuth:
    """GitHub OAuth client supporting Device Flow.

    Usage:
        oauth = GitHubOAuth(client_id="your_client_id")

        # Start device flow
        device = oauth.device_flow_start()
        print(f"Go to {device.verification_uri} and enter: {device.user_code}")

        # Poll for authorization
        token = oauth.device_flow_poll(device)
        print(f"Got token: {token.access_token[:10]}...")
    """

    # GitHub API endpoints
    DEVICE_CODE_URL = "https://github.com/login/device/code"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    API_BASE = "https://api.github.com"

    DEFAULT_SCOPES = ["read:user", "user:email"]

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
    ):
        """Initialize GitHub OAuth client.

        Args:
            client_id: GitHub OAuth App client ID.
            client_secret: GitHub OAuth App client secret (optional for Device Flow).
        """
        self.client_id = client_id
        self.client_secret = client_secret

    def device_flow_start(
        self,
        scopes: Optional[list[str]] = None,
    ) -> DeviceCodeResponse:
        """Start the GitHub Device Flow.

        Args:
            scopes: OAuth scopes to request (default: read:user, user:email).

        Returns:
            DeviceCodeResponse with user_code and verification_uri.
        """
        scopes = scopes or self.DEFAULT_SCOPES

        headers = {"Accept": "application/json"}
        data = {
            "client_id": self.client_id,
            "scope": " ".join(scopes),
        }

        with httpx.Client() as client:
            resp = client.post(
                self.DEVICE_CODE_URL,
                headers=headers,
                data=data,
            )

        if resp.status_code != 200:
            raise GitHubOAuthError(
                f"Device flow start failed: {resp.status_code} {resp.text}"
            )

        result = resp.json()

        if "error" in result:
            raise GitHubOAuthError(f"GitHub error: {result.get('error_description', result['error'])}")

        return DeviceCodeResponse(
            device_code=result["device_code"],
            user_code=result["user_code"],
            verification_uri=result["verification_uri"],
            expires_in=result["expires_in"],
            interval=result.get("interval", 5),
        )

    def device_flow_poll(
        self,
        device_code: str,
        interval: int = 5,
        timeout: int = 900,
    ) -> TokenResponse:
        """Poll GitHub for the Device Flow authorization result.

        Args:
            device_code: The device_code from device_flow_start().
            interval: Minimum polling interval in seconds.
            timeout: Maximum time to wait in seconds.

        Returns:
            TokenResponse with the access token.

        Raises:
            GitHubOAuthError: If authorization fails or times out.
        """
        headers = {"Accept": "application/json"}
        data = {
            "client_id": self.client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        if self.client_secret:
            data["client_secret"] = self.client_secret

        start_time = time.time()
        current_interval = interval

        with httpx.Client() as client:
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise GitHubOAuthError("Device flow timed out waiting for authorization")

                time.sleep(current_interval)

                resp = client.post(
                    self.TOKEN_URL,
                    headers=headers,
                    data=data,
                )

                result = resp.json()

                if resp.status_code == 200 and "access_token" in result:
                    return TokenResponse(
                        access_token=result["access_token"],
                        token_type=result.get("token_type", "bearer"),
                        scope=result.get("scope", ""),
                    )

                error = result.get("error", "")

                if error == "authorization_pending":
                    # Still waiting, keep polling
                    continue
                elif error == "slow_down":
                    # GitHub says we're polling too fast
                    current_interval = result.get("interval", current_interval + 5)
                    continue
                elif error == "expired_token":
                    raise GitHubOAuthError(
                        "Device code expired. Please restart the authorization flow."
                    )
                elif error == "access_denied":
                    raise GitHubOAuthError("User denied the authorization request.")
                else:
                    raise GitHubOAuthError(
                        f"Unexpected error: {error} - {result.get('error_description', '')}"
                    )

    def get_authorization_url(
        self,
        scopes: Optional[list[str]] = None,
        state: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> str:
        """Generate the Authorization Code Flow URL.

        Args:
            scopes: OAuth scopes to request.
            state: Random state string for CSRF protection.
            redirect_uri: Redirect URI after authorization.

        Returns:
            Authorization URL string to open in a browser.
        """
        scopes = scopes or self.DEFAULT_SCOPES

        params = {
            "client_id": self.client_id,
            "scope": " ".join(scopes),
        }

        if state:
            params["state"] = state
        if redirect_uri:
            params["redirect_uri"] = redirect_uri

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZE_URL}?{query}"

    def exchange_code(self, code: str, redirect_uri: Optional[str] = None) -> TokenResponse:
        """Exchange an authorization code for an access token.

        Args:
            code: The authorization code from the redirect.
            redirect_uri: Must match the redirect_uri used in the authorization URL.

        Returns:
            TokenResponse with the access token.

        Raises:
            GitHubOAuthError: If the exchange fails.
        """
        if not self.client_secret:
            raise GitHubOAuthError("Client secret required for Authorization Code Flow")

        headers = {"Accept": "application/json"}
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }

        if redirect_uri:
            data["redirect_uri"] = redirect_uri

        with httpx.Client() as client:
            resp = client.post(self.TOKEN_URL, headers=headers, data=data)

        result = resp.json()

        if "error" in result:
            raise GitHubOAuthError(
                f"Code exchange failed: {result.get('error_description', result['error'])}"
            )

        return TokenResponse(
            access_token=result["access_token"],
            token_type=result.get("token_type", "bearer"),
            scope=result.get("scope", ""),
        )
