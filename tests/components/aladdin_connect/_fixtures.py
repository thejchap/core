"""Tryke fixtures for the Aladdin Connect integration."""

from collections.abc import Generator
from time import time
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.aladdin_connect import DOMAIN
from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from .const import CLIENT_ID, CLIENT_SECRET, USER_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def mock_aladdin_connect_api() -> Generator[AsyncMock]:
    """Mock the AladdinConnectClient."""
    mock_door = AsyncMock()
    mock_door.device_id = "test_device_id"
    mock_door.door_number = 1
    mock_door.name = "Test Door"
    mock_door.status = "closed"
    mock_door.link_status = "connected"
    mock_door.battery_level = 100
    mock_door.unique_id = f"{mock_door.device_id}-{mock_door.door_number}"

    with (
        patch(
            "homeassistant.components.aladdin_connect.AladdinConnectClient",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.aladdin_connect.config_flow.AladdinConnectClient",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.get_doors.return_value = [mock_door]
        yield client


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setup entry."""
    with patch(
        "homeassistant.components.aladdin_connect.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Define a mock config entry fixture."""
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Aladdin Connect",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "old-token",
                "refresh_token": "old-refresh-token",
                "expires_in": 3600,
                "expires_at": time() + 3600,
            },
        },
        source="user",
        unique_id=USER_ID,
    )


@fixture
def use_cloud(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Add cloud component."""
    hass.config.components.add("cloud")


@fixture
async def access_token(hass: HomeAssistant = Depends(hass_fx)) -> str:
    """Return a valid access token with sub field for unique ID."""
    return config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "sub": USER_ID,
            "aud": [],
            "iat": 1234567890,
            "exp": 1234567890 + 3600,
        },
    )
