"""Tests for JustNimbus initialization."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.justnimbus.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import FIXTURE_OLD_USER_INPUT, FIXTURE_UNIQUE_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def config_entry_reauth_at_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that setting up with old config results in reauth."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=FIXTURE_UNIQUE_ID, data=FIXTURE_OLD_USER_INPUT
    )
    mock_config.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config.entry_id)
    await hass.async_block_till_done()

    expect(mock_config.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(any(mock_config.async_get_active_flows(hass, {"reauth"}))).to_be(True)
