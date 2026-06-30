"""Tests for the GitHub OAuth Device Flow client.

httpx is faked via a lightweight stub client so no network calls are made.
"""

import pytest

import src.github.oauth as oauth_mod
from src.github.oauth import GitHubOAuth, GitHubOAuthError, DeviceCodeResponse


class FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or str(payload)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    """Stub for httpx.Client supporting the context-manager + post API.

    Pops one queued response per request, recording the calls made.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, headers=None, data=None):
        self.calls.append((url, data))
        return self._responses.pop(0)


@pytest.fixture
def patch_httpx(monkeypatch):
    """Patch httpx.Client in the oauth module with a queued FakeClient."""

    holder = {}

    def install(responses):
        client = FakeClient(responses)
        holder["client"] = client
        monkeypatch.setattr(oauth_mod.httpx, "Client", lambda *a, **k: client)
        return client

    return install


class TestDeviceFlowStart:
    def test_success(self, patch_httpx):
        patch_httpx(
            [
                FakeResponse(
                    200,
                    {
                        "device_code": "dev123",
                        "user_code": "WDJB-MJHT",
                        "verification_uri": "https://github.com/login/device",
                        "expires_in": 900,
                        "interval": 5,
                    },
                )
            ]
        )
        oauth = GitHubOAuth(client_id="cid")
        device = oauth.device_flow_start()

        assert isinstance(device, DeviceCodeResponse)
        assert device.device_code == "dev123"
        assert device.user_code == "WDJB-MJHT"
        assert device.interval == 5

    def test_default_interval_when_missing(self, patch_httpx):
        patch_httpx(
            [
                FakeResponse(
                    200,
                    {
                        "device_code": "d",
                        "user_code": "u",
                        "verification_uri": "https://x",
                        "expires_in": 900,
                    },
                )
            ]
        )
        device = GitHubOAuth("cid").device_flow_start()
        assert device.interval == 5

    def test_non_200_raises(self, patch_httpx):
        patch_httpx([FakeResponse(404, {}, text="not found")])
        with pytest.raises(GitHubOAuthError, match="Device flow start failed"):
            GitHubOAuth("cid").device_flow_start()

    def test_error_payload_raises(self, patch_httpx):
        patch_httpx(
            [FakeResponse(200, {"error": "bad", "error_description": "nope"})]
        )
        with pytest.raises(GitHubOAuthError, match="nope"):
            GitHubOAuth("cid").device_flow_start()

    def test_scopes_are_sent(self, patch_httpx):
        client = patch_httpx(
            [
                FakeResponse(
                    200,
                    {
                        "device_code": "d",
                        "user_code": "u",
                        "verification_uri": "https://x",
                        "expires_in": 900,
                        "interval": 5,
                    },
                )
            ]
        )
        GitHubOAuth("cid").device_flow_start(scopes=["repo", "read:org"])
        _, data = client.calls[0]
        assert data["scope"] == "repo read:org"
        assert data["client_id"] == "cid"


class TestDeviceFlowPoll:
    @pytest.fixture(autouse=True)
    def _no_sleep(self, monkeypatch):
        # Avoid real delays during polling.
        monkeypatch.setattr(oauth_mod.time, "sleep", lambda *_: None)

    def test_success_after_pending(self, patch_httpx):
        patch_httpx(
            [
                FakeResponse(200, {"error": "authorization_pending"}),
                FakeResponse(
                    200,
                    {
                        "access_token": "ghp_token",
                        "token_type": "bearer",
                        "scope": "read:user",
                    },
                ),
            ]
        )
        token = GitHubOAuth("cid").device_flow_poll("dev123", interval=0)
        assert token.access_token == "ghp_token"
        assert token.token_type == "bearer"
        assert token.scope == "read:user"

    def test_slow_down_increases_interval_and_succeeds(self, patch_httpx):
        patch_httpx(
            [
                FakeResponse(200, {"error": "slow_down", "interval": 7}),
                FakeResponse(200, {"access_token": "t"}),
            ]
        )
        token = GitHubOAuth("cid").device_flow_poll("dev", interval=0)
        assert token.access_token == "t"

    def test_access_denied_raises(self, patch_httpx):
        patch_httpx([FakeResponse(200, {"error": "access_denied"})])
        with pytest.raises(GitHubOAuthError, match="denied"):
            GitHubOAuth("cid").device_flow_poll("dev", interval=0)

    def test_expired_token_raises(self, patch_httpx):
        patch_httpx([FakeResponse(200, {"error": "expired_token"})])
        with pytest.raises(GitHubOAuthError, match="expired"):
            GitHubOAuth("cid").device_flow_poll("dev", interval=0)

    def test_unexpected_error_raises(self, patch_httpx):
        patch_httpx(
            [FakeResponse(200, {"error": "boom", "error_description": "kaboom"})]
        )
        with pytest.raises(GitHubOAuthError, match="boom"):
            GitHubOAuth("cid").device_flow_poll("dev", interval=0)

    def test_client_secret_included_when_present(self, patch_httpx):
        client = patch_httpx([FakeResponse(200, {"access_token": "t"})])
        GitHubOAuth("cid", client_secret="sec").device_flow_poll("dev", interval=0)
        _, data = client.calls[0]
        assert data["client_secret"] == "sec"
        assert data["device_code"] == "dev"


class TestAuthorizationCodeFlow:
    def test_get_authorization_url_contains_params(self):
        url = GitHubOAuth("cid").get_authorization_url(
            scopes=["read:user"], state="xyz", redirect_uri="https://cb"
        )
        assert url.startswith("https://github.com/login/oauth/authorize?")
        assert "client_id=cid" in url
        assert "scope=read:user" in url
        assert "state=xyz" in url
        assert "redirect_uri=https://cb" in url

    def test_exchange_code_requires_secret(self):
        with pytest.raises(GitHubOAuthError, match="secret required"):
            GitHubOAuth("cid").exchange_code("code")

    def test_exchange_code_success(self, patch_httpx):
        patch_httpx(
            [FakeResponse(200, {"access_token": "t", "scope": "read:user"})]
        )
        token = GitHubOAuth("cid", client_secret="sec").exchange_code("code")
        assert token.access_token == "t"
        assert token.scope == "read:user"

    def test_exchange_code_error_raises(self, patch_httpx):
        patch_httpx(
            [FakeResponse(200, {"error": "bad_verification_code",
                                "error_description": "invalid"})]
        )
        with pytest.raises(GitHubOAuthError, match="invalid"):
            GitHubOAuth("cid", client_secret="sec").exchange_code("code")
