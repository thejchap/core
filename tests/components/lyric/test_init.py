"""Tests for the Honeywell Lyric integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.lyric.const import DOMAIN
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
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": 9999999999,
                "token_type": "Bearer",
            },
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
        side_effect=ImplementationUnavailableError,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
