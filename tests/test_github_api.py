"""Tests for the GitHub REST API client.

httpx is faked via a lightweight stub client so no network calls are made.
"""

import pytest

import src.github.api as api_mod
from src.github.api import GitHubAPI, GitHubAPIError, GitHubUser


class FakeResponse:
    def __init__(self, status_code: int, payload, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text or str(payload)

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, headers=None):
        self.calls.append((url, headers))
        return self._response


@pytest.fixture
def patch_httpx(monkeypatch):
    def install(response):
        client = FakeClient(response)
        monkeypatch.setattr(api_mod.httpx, "Client", lambda *a, **k: client)
        return client

    return install


class TestGetUser:
    def test_success_maps_fields(self, patch_httpx):
        client = patch_httpx(
            FakeResponse(
                200,
                {
                    "login": "octocat",
                    "name": "The Octocat",
                    "email": "octo@github.com",
                    "avatar_url": "https://avatar",
                    "two_factor_authentication": True,
                    "id": 42,
                },
            )
        )
        user = GitHubAPI().get_user("tok")

        assert isinstance(user, GitHubUser)
        assert user.login == "octocat"
        assert user.name == "The Octocat"
        assert user.email == "octo@github.com"
        assert user.two_factor_enabled is True
        assert user.id == 42

        # Authorization header carries the bearer token.
        _, headers = client.calls[0]
        assert headers["Authorization"] == "Bearer tok"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"

    def test_missing_optional_fields_default(self, patch_httpx):
        patch_httpx(FakeResponse(200, {"login": "u", "id": 1}))
        user = GitHubAPI().get_user("tok")
        assert user.name is None
        assert user.email is None
        assert user.avatar_url == ""
        assert user.two_factor_enabled is False

    def test_non_200_raises(self, patch_httpx):
        patch_httpx(FakeResponse(401, {}, text="unauthorized"))
        with pytest.raises(GitHubAPIError, match="Failed to get user"):
            GitHubAPI().get_user("tok")


class TestCheck2FAStatus:
    def test_enabled(self, patch_httpx):
        patch_httpx(
            FakeResponse(
                200,
                {"login": "u", "id": 1, "two_factor_authentication": True},
            )
        )
        status = GitHubAPI().check_2fa_status("tok")
        assert status == {"login": "u", "two_factor_enabled": True, "has_totp": True}

    def test_disabled_has_totp_none(self, patch_httpx):
        patch_httpx(
            FakeResponse(
                200,
                {"login": "u", "id": 1, "two_factor_authentication": False},
            )
        )
        status = GitHubAPI().check_2fa_status("tok")
        assert status["two_factor_enabled"] is False
        assert status["has_totp"] is None


class TestListOrgs:
    def test_success(self, patch_httpx):
        patch_httpx(FakeResponse(200, [{"login": "acme"}, {"login": "globex"}]))
        orgs = GitHubAPI().list_orgs("tok")
        assert [o["login"] for o in orgs] == ["acme", "globex"]

    def test_failure_raises(self, patch_httpx):
        patch_httpx(FakeResponse(500, []))
        with pytest.raises(GitHubAPIError, match="Failed to list orgs"):
            GitHubAPI().list_orgs("tok")


class TestGetUserEmails:
    def test_success(self, patch_httpx):
        patch_httpx(
            FakeResponse(
                200,
                [{"email": "a@b.com", "primary": True, "verified": True}],
            )
        )
        emails = GitHubAPI().get_user_emails("tok")
        assert emails[0]["email"] == "a@b.com"
        assert emails[0]["primary"] is True

    def test_failure_raises(self, patch_httpx):
        patch_httpx(FakeResponse(403, []))
        with pytest.raises(GitHubAPIError, match="Failed to get emails"):
            GitHubAPI().get_user_emails("tok")
