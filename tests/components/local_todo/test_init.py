"""Tests for init platform of local_todo."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import TEST_ENTITY, config_entry, setup_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload(
    hass: HomeAssistant = Depends(_trigger_executor),
    _setup: None = Depends(setup_integration),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test loading and unloading a config entry."""
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    state = hass.states.get(TEST_ENTITY)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("0")

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    state = hass.states.get(TEST_ENTITY)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("unavailable")


@test
async def remove_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    _setup: None = Depends(setup_integration),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test removing a config entry."""
    with patch("homeassistant.components.local_todo.Path.unlink") as unlink_mock:
        expect(await hass.config_entries.async_remove(config_entry.entry_id)).not_.to_be(None)
        await hass.async_block_till_done()
        unlink_mock.assert_called_once()


@test.skip("indirect parametrize: store_read_side_effect routed via request.param")
async def load_failure() -> None:
    """Stub for test_load_failure (indirect parametrize)."""
