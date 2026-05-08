"""Tests for the microBees component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.microbees.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from ._fixtures import config_entry, expires_at, scopes

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture anchor."""


@test
async def migrate_entry_minor_version_1_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrating a 1.1 config entry to 1.2."""
    with patch(
        "homeassistant.components.microbees.async_setup_entry", return_value=True
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "auth_implementation": DOMAIN,
                "token": {
                    "refresh_token": "mock-refresh-token",
                    "access_token": "mock-access-token",
                    "type": "Bearer",
                    "expires_in": 60,
                },
            },
            version=1,
            minor_version=1,
            unique_id=54321,
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        expect(entry.version).to_equal(1)
        expect(entry.minor_version).to_equal(2)
        expect(entry.unique_id).to_equal("54321")


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
