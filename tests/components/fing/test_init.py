"""Test the Fing integration init."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.fing.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import (
    make_mock_config_entry,
    make_mocked_fing_agent,
    mock_config_entry,
    mocked_fing_agent,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.cases(
    test.case("new", api_type="new", expected=ConfigEntryState.LOADED),
    test.case("old", api_type="old", expected=ConfigEntryState.SETUP_ERROR),
)
async def setup_entry_new_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    api_type: str,
    expected: ConfigEntryState,
) -> None:
    """Test setup Fing Agent."""
    entry = make_mock_config_entry(api_type)
    # Build a fresh mocked agent for this api_type
    agent_gen = make_mocked_fing_agent(api_type)
    agent = next(agent_gen)
    try:
        result = await init_integration(hass, entry, agent)
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(result.state).to_be(expected)
    finally:
        try:
            next(agent_gen)
        except StopIteration:
            pass


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    agent: MagicMock = Depends(mocked_fing_agent),
) -> None:
    """Test unload of entry."""
    result = await init_integration(hass, entry, agent)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(result.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(result.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(result.state).to_be(ConfigEntryState.NOT_LOADED)
