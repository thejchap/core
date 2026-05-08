"""Test the Dexcom config flow."""

from unittest.mock import patch

from pydexcom.errors import AccountError, SessionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.dexcom.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import CONFIG, init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def setup_entry_account_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entry setup failed due to account error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_username",
        unique_id="test_username",
        data=CONFIG,
        options=None,
    )
    with patch(
        "homeassistant.components.dexcom.Dexcom",
        side_effect=AccountError,
    ):
        entry.add_to_hass(hass)
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(result).to_be(False)


@test
async def setup_entry_session_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entry setup failed due to session error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_username",
        unique_id="test_username",
        data=CONFIG,
        options=None,
    )
    with patch(
        "homeassistant.components.dexcom.Dexcom",
        side_effect=SessionError,
    ):
        entry.add_to_hass(hass)
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(result).to_be(False)


@test
async def unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)
