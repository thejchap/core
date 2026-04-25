"""Tryke fixtures for the Twitch integration."""

from collections.abc import Generator
import time
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture
from twitchAPI.object.api import FollowedChannel, Stream, TwitchUser, UserSubscription

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.twitch.const import DOMAIN, OAUTH2_TOKEN, OAUTH_SCOPES
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import TwitchIterObject, get_generator

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    hass as hass_fx,
)
from tests.test_util.aiohttp import AiohttpClientMocker

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
TITLE = "Test"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.twitch.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def scopes() -> list[str]:
    """Set the scopes present in the OAuth token."""
    return [scope.value for scope in OAUTH_SCOPES]


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials so the OAuth flow finds the client id."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration timestamp."""
    return time.time() + 3600


@fixture
def mock_config_entry(
    expires_at: int = Depends(expires_at),
    scopes: list[str] = Depends(scopes),
) -> MockConfigEntry:
    """Create Twitch entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id="123",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": " ".join(scopes),
            },
        },
        options={"channels": ["internetofthings"]},
    )


@fixture
def mock_connection(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> AiohttpClientMocker:
    """Mock Twitch OAuth token endpoint."""
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    return aioclient_mock


@fixture
def twitch_mock(hass: HomeAssistant = Depends(hass_fx)) -> Generator[AsyncMock]:
    """Mock the Twitch SDK client."""
    with (
        patch(
            "homeassistant.components.twitch.Twitch",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.twitch.config_flow.Twitch",
            new=mock_client,
        ),
    ):
        mock_client.return_value.get_users = lambda *args, **kwargs: get_generator(
            hass, "get_users.json", TwitchUser
        )
        mock_client.return_value.get_followed_channels.return_value = TwitchIterObject(
            hass, "get_followed_channels.json", FollowedChannel
        )
        mock_client.return_value.get_followed_streams.return_value = get_generator(
            hass, "get_followed_streams.json", Stream
        )
        mock_client.return_value.check_user_subscription.return_value = (
            UserSubscription(
                **load_json_object_fixture("check_user_subscription.json", DOMAIN)
            )
        )
        mock_client.return_value.has_required_auth.return_value = True
        yield mock_client
