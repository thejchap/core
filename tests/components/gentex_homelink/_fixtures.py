"""Tryke fixtures for Gentex HomeLink tests."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.gentex_homelink.const import DOMAIN, OAUTH2_TOKEN_URL

from . import TEST_ACCESS_JWT, TEST_UNIQUE_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fx
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def mock_srp_access_token() -> str:
    """Return preferred JWT for mock SRP auth requests."""
    return TEST_ACCESS_JWT


@fixture
def mock_srp_auth(
    access_token: str = Depends(mock_srp_access_token),
) -> Generator[AsyncMock]:
    """Mock SRP authentication."""
    with patch(
        "homeassistant.components.gentex_homelink.config_flow.SRPAuth"
    ) as mock_srp_auth:
        instance = mock_srp_auth.return_value
        instance.async_get_access_token.return_value = {
            "AuthenticationResult": {
                "AccessToken": access_token,
                "RefreshToken": "refresh",
                "TokenType": "bearer",
                "ExpiresIn": 3600,
            }
        }
        yield instance


@fixture
def aioclient_mock_post_token(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> AiohttpClientMocker:
    """Provide an aioclient mocker pre-seeded with the OAuth2 token URL."""
    aioclient_mock.post(OAUTH2_TOKEN_URL, status=HTTPStatus.OK, json={})
    return aioclient_mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock setup entry."""
    return MockConfigEntry(
        unique_id=TEST_UNIQUE_ID,
        version=1,
        domain=DOMAIN,
        data={
            "auth_implementation": "gentex_homelink",
            "token": {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "expires_at": 1234567890,
            },
        },
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setup entry."""
    with patch(
        "homeassistant.components.gentex_homelink.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
