"""Tryke fixtures for microBees tests."""

import time
from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from microBeesPy import Bee, MicroBees, Profile
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.microbees.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fixture

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
TITLE = "MicroBees"
MICROBEES_AUTH_URI = "https://dev.microbees.com/oauth/authorize"
MICROBEES_TOKEN_URI = "https://dev.microbees.com/oauth/token"

SCOPES = ["read", "write"]


@fixture
def scopes() -> list[str]:
    """Return scopes for the OAuth token."""
    return SCOPES


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set up application credentials."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


@fixture
def expires_at() -> int:
    """Set the OAuth token expiration time."""
    return int(time.time() + 3600)


@fixture
def config_entry(
    expires_at_value: int = Depends(expires_at),
    scopes_value: list[str] = Depends(scopes),
) -> MockConfigEntry:
    """Mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id="54321",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at_value,
                "scope": " ".join(scopes_value),
            },
        },
    )


@fixture
def microbees() -> Generator[AsyncMock]:
    """Mock microbees client."""
    devices_json = load_json_array_fixture("microbees/bees.json")
    devices = [Bee.from_dict(device) for device in devices_json]
    profile_json = load_json_object_fixture("microbees/profile.json")
    profile = Profile.from_dict(profile_json)
    mock = AsyncMock(spec=MicroBees)
    mock.getBees.return_value = devices
    mock.getMyProfile.return_value = profile

    with (
        patch(
            "homeassistant.components.microbees.config_flow.MicroBees",
            return_value=mock,
        ) as mock,
        patch(
            "homeassistant.components.microbees.MicroBees",
            return_value=mock,
        ),
    ):
        yield mock
