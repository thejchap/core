"""Test the Devialet init."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import DOMAIN as MP_DOMAIN, MediaPlayerState
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import NAME, setup_integration

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the Devialet configuration entry loading and unloading."""
    entry = await setup_integration(hass, aioclient_mock)

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.unique_id is not None).to_be(True)

    state = hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}")
    expect(state.state).to_equal(MediaPlayerState.PLAYING)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def load_unload_config_entry_when_device_unavailable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test the Devialet config entry loading and unloading when unavailable."""
    entry = await setup_integration(hass, aioclient_mock, state="unavailable")

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(entry.unique_id is not None).to_be(True)

    state = hass.states.get(f"{MP_DOMAIN}.{NAME.lower()}")
    expect(state.state).to_equal("unavailable")

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
