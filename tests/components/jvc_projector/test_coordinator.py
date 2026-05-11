"""Tests for JVC Projector config entry."""

from datetime import timedelta
from unittest.mock import patch

from jvcprojector import (
    Command,
    JvcProjectorCommandError,
    JvcProjectorTimeoutError,
    command as cmd,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.jvc_projector.coordinator import (
    INTERVAL_FAST,
    INTERVAL_SLOW,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.util.dt import utcnow

from . import MOCK_HOST, MOCK_MAC, MOCK_MODEL, MOCK_PASSWORD, MOCK_PORT
from ._fixtures import CAPABILITIES, FIXTURES

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture so tryke resolves Depends() per the migration pattern."""


async def _setup_with_fixture(
    hass: HomeAssistant,
    *,
    fixture_name: str = "on",
    fixture_override: dict[type[Command], str | type[Exception]] | None = None,
) -> MockConfigEntry:
    """Set up the config entry with a chosen fixture profile (no indirect parametrize)."""
    fixture_data = FIXTURES[fixture_name].copy()
    if fixture_override:
        fixture_data.update(fixture_override)

    async def device_get(command):
        if command in fixture_data:
            value = fixture_data[command]
            if isinstance(value, type) and issubclass(value, Exception):
                raise value
            return value
        raise ValueError(f"Test fixture failure; unexpected command {command}")

    config_entry = MockConfigEntry(
        domain="jvc_projector",
        unique_id=format_mac(MOCK_MAC),
        version=1,
        data={
            "host": MOCK_HOST,
            "port": MOCK_PORT,
            "password": MOCK_PASSWORD,
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.jvc_projector.JvcProjector",
            autospec=True,
        ) as setup_mock,
        patch(
            "homeassistant.components.jvc_projector.coordinator.TIMEOUT_RETRIES", 2
        ),
        patch(
            "homeassistant.components.jvc_projector.coordinator.TIMEOUT_SLEEP", 0.1
        ),
    ):
        device = setup_mock.return_value
        device.ip = MOCK_HOST
        device.host = MOCK_HOST
        device.port = MOCK_PORT
        device.mac = MOCK_MAC
        device.model = MOCK_MODEL
        device.get.side_effect = device_get
        device.capabilities.return_value = CAPABILITIES
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    return config_entry


@test
async def coordinator_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test coordinator update runs."""
    config_entry = await _setup_with_fixture(hass, fixture_name="standby")
    async_fire_time_changed(
        hass, utcnow() + timedelta(seconds=INTERVAL_SLOW.seconds + 1)
    )
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data
    expect(coordinator.update_interval).to_be(INTERVAL_SLOW)


@test
async def coordinator_device_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test coordinator changes update interval when device is on."""
    config_entry = await _setup_with_fixture(hass, fixture_name="on")
    coordinator = config_entry.runtime_data
    expect(coordinator.update_interval).to_be(INTERVAL_FAST)


@test
async def coordinator_setup_connect_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test coordinator connect error."""
    config_entry = await _setup_with_fixture(
        hass, fixture_override={cmd.Power: JvcProjectorTimeoutError}
    )
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def coordinator_setup_power_command_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test coordinator fails setup when Power command errors with no cached value."""
    config_entry = await _setup_with_fixture(
        hass, fixture_override={cmd.Power: JvcProjectorCommandError}
    )
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def coordinator_command_error_keeps_other_entities_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a failing command does not take every entity offline."""
    config_entry = await _setup_with_fixture(
        hass, fixture_override={cmd.Input: JvcProjectorCommandError}
    )
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    coordinator = config_entry.runtime_data
    expect(coordinator.last_update_success).to_be(True)

    power = hass.states.get("sensor.jvc_projector_status")
    expect(power is not None).to_be(True)
    expect(power.state).to_equal("on")

    light_time = hass.states.get("sensor.jvc_projector_light_time")
    expect(light_time is not None).to_be(True)
    expect(light_time.state != STATE_UNAVAILABLE).to_be(True)
