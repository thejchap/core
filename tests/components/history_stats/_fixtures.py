"""Tryke fixtures for the History stats integration."""

from collections.abc import Generator
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.history_stats.config_flow import (
    HistoryStatsConfigFlowHandler,
)
from homeassistant.components.history_stats.const import (
    CONF_END,
    CONF_START,
    DEFAULT_NAME,
    DOMAIN,
)
from homeassistant.components.sensor import CONF_STATE_CLASS
from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_STATE, CONF_TYPE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Automatically patch history stats setup."""
    with patch(
        "homeassistant.components.history_stats.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


@fixture
def sensor_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Fixture to create a sensor config entry."""
    sensor_config_entry = MockConfigEntry()
    sensor_config_entry.add_to_hass(hass)
    return sensor_config_entry


@fixture
def sensor_device(
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    config_entry: ConfigEntry = Depends(sensor_config_entry),
) -> dr.DeviceEntry:
    """Fixture to create a sensor device."""
    return device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )


@fixture
def sensor_entity_entry(
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    config_entry: ConfigEntry = Depends(sensor_config_entry),
    device: dr.DeviceEntry = Depends(sensor_device),
) -> er.RegistryEntry:
    """Fixture to create a sensor entity entry."""
    return entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique",
        config_entry=config_entry,
        device_id=device.id,
        original_name="ABC",
    )


@fixture
def history_stats_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> MockConfigEntry:
    """Fixture to create a history_stats config entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: entity_entry.entity_id,
            CONF_STATE: ["on"],
            CONF_TYPE: "count",
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
        },
        title="My history stats",
        version=HistoryStatsConfigFlowHandler.VERSION,
        minor_version=HistoryStatsConfigFlowHandler.MINOR_VERSION,
    )

    config_entry.add_to_hass(hass)

    return config_entry


@fixture
def get_config() -> dict[str, Any]:
    """Return configuration for loaded_entry."""
    return {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "binary_sensor.test_monitored",
        CONF_STATE: ["on"],
        CONF_TYPE: "count",
        CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
        CONF_END: "{{ utcnow() }}",
        CONF_STATE_CLASS: "measurement",
    }


@fixture
async def loaded_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(get_config),
) -> MockConfigEntry:
    """Set up the History stats integration in Home Assistant."""
    start_time = dt_util.utcnow() - timedelta(minutes=60)
    t0 = start_time + timedelta(minutes=20)
    t1 = t0 + timedelta(minutes=10)
    t2 = t1 + timedelta(minutes=10)

    def _fake_states(*args, **kwargs):
        return {
            "binary_sensor.test_monitored": [
                State("binary_sensor.test_monitored", "off", last_changed=start_time),
                State("binary_sensor.test_monitored", "on", last_changed=t0),
                State("binary_sensor.test_monitored", "off", last_changed=t1),
                State("binary_sensor.test_monitored", "on", last_changed=t2),
            ]
        }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_NAME,
        source=SOURCE_USER,
        options=config,
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.recorder.history.state_changes_during_period",
        _fake_states,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        await async_update_entity(hass, "sensor.test")
        await hass.async_block_till_done()

    return config_entry
