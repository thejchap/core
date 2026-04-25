"""Tryke fixtures for Elexa Guardian tests."""

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.guardian import CONF_UID, DOMAIN
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fx


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.guardian.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PORT: 7777,
    }


@fixture
def unique_id() -> str:
    """Define a config entry unique ID fixture."""
    return "guardian_3456"


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fx),
    config: dict[str, Any] = Depends(config),
    unique_id: str = Depends(unique_id),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        data={CONF_UID: "3456", **config},
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def data_sensor_pair_dump() -> JsonObjectType:
    """Define data from a successful sensor_pair_dump response."""
    return load_json_object_fixture("sensor_pair_dump_data.json", "guardian")


@fixture
def data_sensor_pair_sensor() -> JsonObjectType:
    """Define data from a successful sensor_pair_sensor response."""
    return load_json_object_fixture("sensor_pair_sensor_data.json", "guardian")


@fixture
def data_sensor_paired_sensor_status() -> JsonObjectType:
    """Define data from a successful sensor_paired_sensor_status response."""
    return load_json_object_fixture("sensor_paired_sensor_status_data.json", "guardian")


@fixture
def data_system_diagnostics() -> JsonObjectType:
    """Define data from a successful system_diagnostics response."""
    return load_json_object_fixture("system_diagnostics_data.json", "guardian")


@fixture
def data_system_onboard_sensor_status() -> JsonObjectType:
    """Define data from a successful system_onboard_sensor_status response."""
    return load_json_object_fixture(
        "system_onboard_sensor_status_data.json", "guardian"
    )


@fixture
def data_system_ping() -> JsonObjectType:
    """Define data from a successful system_ping response."""
    return load_json_object_fixture("system_ping_data.json", "guardian")


@fixture
def data_valve_status() -> JsonObjectType:
    """Define data from a successful valve_status response."""
    return load_json_object_fixture("valve_status_data.json", "guardian")


@fixture
def data_wifi_status() -> JsonObjectType:
    """Define data from a successful wifi_status response."""
    return load_json_object_fixture("wifi_status_data.json", "guardian")


@fixture
async def setup_guardian(
    hass: HomeAssistant = Depends(hass_fx),
    config: dict[str, Any] = Depends(config),
    data_sensor_pair_dump: JsonObjectType = Depends(data_sensor_pair_dump),
    data_sensor_pair_sensor: JsonObjectType = Depends(data_sensor_pair_sensor),
    data_sensor_paired_sensor_status: JsonObjectType = Depends(
        data_sensor_paired_sensor_status
    ),
    data_system_diagnostics: JsonObjectType = Depends(data_system_diagnostics),
    data_system_onboard_sensor_status: JsonObjectType = Depends(
        data_system_onboard_sensor_status
    ),
    data_system_ping: JsonObjectType = Depends(data_system_ping),
    data_valve_status: JsonObjectType = Depends(data_valve_status),
    data_wifi_status: JsonObjectType = Depends(data_wifi_status),
) -> AsyncGenerator[None]:
    """Define a fixture to set up Guardian."""
    with (
        patch("aioguardian.client.Client.connect"),
        patch(
            "aioguardian.commands.sensor.SensorCommands.pair_dump",
            return_value=data_sensor_pair_dump,
        ),
        patch(
            "aioguardian.commands.sensor.SensorCommands.pair_sensor",
            return_value=data_sensor_pair_sensor,
        ),
        patch(
            "aioguardian.commands.sensor.SensorCommands.paired_sensor_status",
            return_value=data_sensor_paired_sensor_status,
        ),
        patch(
            "aioguardian.commands.system.SystemCommands.diagnostics",
            return_value=data_system_diagnostics,
        ),
        patch(
            "aioguardian.commands.system.SystemCommands.onboard_sensor_status",
            return_value=data_system_onboard_sensor_status,
        ),
        patch(
            "aioguardian.commands.system.SystemCommands.ping",
            return_value=data_system_ping,
        ),
        patch(
            "aioguardian.commands.valve.ValveCommands.status",
            return_value=data_valve_status,
        ),
        patch(
            "aioguardian.commands.wifi.WiFiCommands.status",
            return_value=data_wifi_status,
        ),
        patch(
            "aioguardian.client.Client.disconnect",
        ),
        patch(
            "homeassistant.components.guardian.PLATFORMS",
            [],
        ),
    ):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()
        yield
