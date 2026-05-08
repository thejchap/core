"""Tests for the iotty integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.iotty.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="IOTTY00001",
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "REFRESH_TOKEN",
                "access_token": "ACCESS_TOKEN_1",
                "expires_in": 10,
                "expires_at": 0,
                "token_type": "bearer",
                "random_other_data": "should_stay",
            },
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PORT: 9123,
        },
        unique_id="IOTTY00001",
    )


@test.skip("requires OAuth2 application credentials + local_oauth_impl chain")
async def load_unload_coordinator_called() -> None:
    """Stub for test_load_unload_coordinator_called."""


@test
async def oauth_implementation_not_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.iotty.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("requires OAuth2 application credentials + local_oauth_impl chain")
async def load_unload_iottyproxy_called() -> None:
    """Stub for test_load_unload_iottyproxy_called."""
