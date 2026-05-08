"""Tryke fixtures for the fitbit integration."""

from collections.abc import Generator
from http import HTTPStatus
import time
from typing import Any

from tryke import Depends, fixture

from homeassistant.components.fitbit.const import DOMAIN, OAUTH_SCOPES
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.hass_tryke_helpers import setup_application_credentials
from tests.test_util.aiohttp import AiohttpClientMocker

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
PROFILE_USER_ID = "fitbit-api-user-id-1"
FAKE_ACCESS_TOKEN = "some-access-token"
FAKE_REFRESH_TOKEN = "some-refresh-token"
FAKE_AUTH_IMPL = "conftest-imported-cred"
FULL_NAME = "First Last"
DISPLAY_NAME = "First L."
PROFILE_DATA = {
    "fullName": FULL_NAME,
    "displayName": DISPLAY_NAME,
    "displayNameSetting": "name",
    "firstName": "First",
    "lastName": "Last",
}

PROFILE_API_URL = "https://api.fitbit.com/1/user/-/profile.json"
DEVICES_API_URL = "https://api.fitbit.com/1/user/-/devices.json"

SERVER_ACCESS_TOKEN = {
    "refresh_token": "server-refresh-token",
    "access_token": "server-access-token",
    "type": "Bearer",
    "expires_in": 60,
    "scope": " ".join(OAUTH_SCOPES),
}


@fixture
async def setup_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up application credentials for OAuth2."""
    await setup_application_credentials(
        hass, DOMAIN, CLIENT_ID, CLIENT_SECRET, FAKE_AUTH_IMPL
    )


@fixture
def config_entry() -> MockConfigEntry:
    """Fixture for a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": FAKE_AUTH_IMPL,
            "token": {
                "access_token": FAKE_ACCESS_TOKEN,
                "refresh_token": FAKE_REFRESH_TOKEN,
                "scope": " ".join(OAUTH_SCOPES),
                "token_type": "Bearer",
                "expires_at": time.time() + 86400,
            },
        },
        unique_id=PROFILE_USER_ID,
        title=DISPLAY_NAME,
    )


@fixture
def profile(
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> Generator[None]:
    """Fixture to setup fake profile request."""
    profile_response: dict[str, Any] = {
        "user": {
            "encodedId": PROFILE_USER_ID,
            "locale": "en_US",
            **PROFILE_DATA,
        },
    }
    aioclient.get(
        PROFILE_API_URL,
        status=HTTPStatus.OK,
        json=profile_response,
    )
    aioclient.get(
        DEVICES_API_URL,
        status=HTTPStatus.OK,
        json=[],
    )
    yield
