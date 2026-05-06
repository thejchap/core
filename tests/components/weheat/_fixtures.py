"""Tryke fixtures for the Weheat integration."""

from collections.abc import Generator
from time import time
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture
from weheat.abstractions.discovery import HeatPumpDiscovery

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.weheat.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .const import (
    CLIENT_ID,
    CLIENT_SECRET,
    TEST_HP_UUID,
    TEST_MODEL,
    TEST_SN,
    USER_UUID_1,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials so the OAuth flow finds the client id."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock a successful setup."""
    with patch(
        "homeassistant.components.weheat.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_heat_pump_info() -> HeatPumpDiscovery.HeatPumpInfo:
    """Create a HeatPumpInfo with default settings."""
    return HeatPumpDiscovery.HeatPumpInfo(TEST_HP_UUID, None, TEST_MODEL, TEST_SN, True)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Weheat",
        data={
            "id": "12345",
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 60,
            },
        },
        unique_id="123456789",
    )


@fixture
def mock_user_id() -> Generator[AsyncMock]:
    """Mock the user API call."""
    with patch(
        "homeassistant.components.weheat.config_flow.async_get_user_id_from_token",
        return_value=USER_UUID_1,
    ) as user_mock:
        yield user_mock


@fixture
def mock_weheat_discover(
    mock_heat_pump_info: HeatPumpDiscovery.HeatPumpInfo = Depends(mock_heat_pump_info),
) -> Generator[AsyncMock]:
    """Mock a Weheat discovery."""
    with patch(
        "homeassistant.components.weheat.HeatPumpDiscovery.async_discover_active",
        autospec=True,
    ) as mock_discover:
        mock_discover.return_value = [mock_heat_pump_info]
        yield mock_discover
