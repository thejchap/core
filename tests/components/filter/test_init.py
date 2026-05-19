"""Test Filter component setup process."""

from tryke import Depends, fixture, test

from homeassistant.components.filter.const import (
    CONF_FILTER_NAME,
    CONF_FILTER_PRECISION,
    CONF_FILTER_RADIUS,
    CONF_FILTER_WINDOW_SIZE,
    DEFAULT_FILTER_RADIUS,
    DEFAULT_NAME,
    DEFAULT_PRECISION,
    DEFAULT_WINDOW_SIZE,
    DOMAIN,
    FILTER_NAME_OUTLIER,
)
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from ._fixtures import recorder_mock

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Tryke executor trigger for async fixtures with Depends."""
    return 0


@fixture
async def loaded_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder=Depends(recorder_mock),
) -> MockConfigEntry:
    """Set up the Filter integration in Home Assistant."""
    from datetime import timedelta

    config = {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "sensor.test_monitored",
        CONF_FILTER_NAME: FILTER_NAME_OUTLIER,
        CONF_FILTER_WINDOW_SIZE: DEFAULT_WINDOW_SIZE,
        CONF_FILTER_RADIUS: DEFAULT_FILTER_RADIUS,
        CONF_FILTER_PRECISION: DEFAULT_PRECISION,
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options=config,
        entry_id="1",
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    raw_values = [20, 19, 18, 21, 22, 0]
    timestamp = dt_util.utcnow()
    values = []
    for val in raw_values:
        values.append(State("sensor.test_monitored", str(val), last_updated=timestamp))
        timestamp += timedelta(minutes=1)

    for value in values:
        hass.states.async_set(config[CONF_ENTITY_ID], value.state)
        await hass.async_block_till_done()
    await hass.async_block_till_done()

    return config_entry


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    loaded_entry: MockConfigEntry = Depends(loaded_entry),
) -> None:
    """Test unload an entry."""
    assert loaded_entry.state is ConfigEntryState.LOADED
    assert await hass.config_entries.async_unload(loaded_entry.entry_id)
    await hass.async_block_till_done()
    assert loaded_entry.state is ConfigEntryState.NOT_LOADED
