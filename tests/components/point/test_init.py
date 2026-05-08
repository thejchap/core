"""Tests for the Point component."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.point import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture anchor."""


@test
async def oauth_implementation_not_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that unavailable OAuth implementation raises ConfigEntryNotReady."""
    config_entry = MockConfigEntry(
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
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.point.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
