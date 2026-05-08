"""Test fitbit component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from ._fixtures import config_entry, setup_credentials

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
) -> None:
    """Anchor for tryke fixture resolution + creds."""


@test
async def oauth_implementation_not_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("requires integration_setup callable + profile/devices fixtures")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("requires aioclient_mock + integration_setup + profile_id parametrize")
async def token_refresh_failure() -> None:
    """Stub for test_token_refresh_failure."""


@test.skip("requires aioclient_mock + integration_setup")
async def token_refresh_success() -> None:
    """Stub for test_token_refresh_success."""


@test.skip("requires aioclient_mock + integration_setup")
async def token_requires_reauth() -> None:
    """Stub for test_token_requires_reauth."""


@test.skip("requires integration_setup + freezer + device update")
async def device_update_coordinator_failure() -> None:
    """Stub for test_device_update_coordinator_failure."""


@test.skip("requires integration_setup + freezer + device update + reauth")
async def device_update_coordinator_reauth() -> None:
    """Stub for test_device_update_coordinator_reauth."""
