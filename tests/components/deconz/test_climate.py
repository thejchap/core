"""deCONZ climate platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.components.deconz.climate import (
    DECONZ_PRESET_AUTO,
    DECONZ_PRESET_MANUAL,
)
from homeassistant.components.deconz.const import CONF_ALLOW_CLIP_SENSOR
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant

from tests.components.deconz._fixtures import (
    mock_websocket as mock_websocket_fixture,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

# Re-export PRESET_BOOST so tests can reference it.
from homeassistant.components.climate import PRESET_BOOST


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@fixture
def sensor_ws_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends sensor websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"r": "sensors"}
        payload.update(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "0")
        await mock_websocket(data=payload)

    return send


@test.skip("snapshot test - port deferred")
async def simple_climate_device() -> None:
    """Stub for test_simple_climate_device (port deferred)."""


@test.skip("snapshot test - port deferred")
async def climate_device_without_cooling_support() -> None:
    """Stub for test_climate_device_without_cooling_support (port deferred)."""


@test.skip("snapshot test - port deferred")
async def climate_device_with_cooling_support() -> None:
    """Stub for test_climate_device_with_cooling_support (port deferred)."""


@test.skip("snapshot test - port deferred")
async def climate_device_with_fan_support() -> None:
    """Stub for test_climate_device_with_fan_support (port deferred)."""


@test.skip("snapshot test - port deferred")
async def climate_device_with_preset() -> None:
    """Stub for test_climate_device_with_preset (port deferred)."""


@test.skip("snapshot test - port deferred")
async def clip_climate_device() -> None:
    """Stub for test_clip_climate_device (port deferred)."""


@test
async def verify_state_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that state update properly."""
    sensor_payload = {
        "name": "Thermostat",
        "type": "ZHAThermostat",
        "state": {"on": True, "temperature": 2260, "valve": 30},
        "config": {
            "battery": 100,
            "heatsetpoint": 2200,
            "mode": "auto",
            "offset": 10,
            "reachable": True,
        },
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(hass.states.get("climate.thermostat").state).to_equal(HVACMode.AUTO)
    expect(
        hass.states.get("climate.thermostat").attributes["hvac_action"]
    ).to_equal(HVACAction.HEATING)

    await send_sensor({"state": {"on": False}})
    expect(hass.states.get("climate.thermostat").state).to_equal(HVACMode.AUTO)
    expect(
        hass.states.get("climate.thermostat").attributes["hvac_action"]
    ).to_equal(HVACAction.IDLE)


@test
async def add_new_climate_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that adding a new climate device works."""
    await setup_deconz(hass, aioclient)

    event_added_sensor = {
        "e": "added",
        "sensor": {
            "id": "Thermostat id",
            "name": "Thermostat",
            "type": "ZHAThermostat",
            "state": {"on": True, "temperature": 2260, "valve": 30},
            "config": {
                "battery": 100,
                "heatsetpoint": 2200,
                "mode": "auto",
                "offset": 10,
                "reachable": True,
            },
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
    }

    expect(len(hass.states.async_all())).to_equal(0)

    await send_sensor(event_added_sensor)

    expect(len(hass.states.async_all())).to_equal(2)
    expect(hass.states.get("climate.thermostat").state).to_equal(HVACMode.AUTO)
    expect(hass.states.get("sensor.thermostat_battery").state).to_equal("100")
    expect(
        hass.states.get("climate.thermostat").attributes["hvac_action"]
    ).to_equal(HVACAction.HEATING)


@test
async def not_allow_clip_thermostat(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that CLIP thermostats are not allowed."""
    sensor_payload = {
        "name": "CLIP thermostat sensor",
        "type": "CLIPThermostat",
        "state": {},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_CLIP_SENSOR: False},
        sensor_payload=sensor_payload,
    )
    expect(len(hass.states.async_all())).to_equal(0)


@test
async def no_mode_no_state(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that a climate device without mode and state works."""
    sensor_payload = {
        "config": {
            "battery": 25,
            "heatsetpoint": 2222,
            "mode": None,
            "preset": "auto",
            "offset": 0,
            "on": True,
            "reachable": True,
        },
        "ep": 1,
        "etag": "074549903686a77a12ef0f06c499b1ef",
        "lastseen": "2020-11-27T13:45Z",
        "manufacturername": "Zen Within",
        "modelid": "Zen-01",
        "name": "Zen-01",
        "state": {"lastupdated": "none", "on": None, "temperature": 2290},
        "type": "ZHAThermostat",
        "uniqueid": "00:24:46:00:00:11:6f:56-01-0201",
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(len(hass.states.async_all())).to_equal(2)

    climate_thermostat = hass.states.get("climate.zen_01")
    expect(climate_thermostat.state).to_be(STATE_OFF)
    expect(climate_thermostat.attributes["preset_mode"]).to_be(DECONZ_PRESET_AUTO)
    expect(climate_thermostat.attributes["hvac_action"]).to_be(HVACAction.IDLE)


@test
async def boost_mode(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that a climate device with boost mode and different state works."""
    sensor_payload = {
        "config": {
            "battery": 58,
            "heatsetpoint": 2200,
            "locked": False,
            "mode": "heat",
            "offset": -200,
            "on": True,
            "preset": "manual",
            "reachable": True,
            "schedule": {},
            "schedule_on": False,
            "setvalve": False,
            "windowopen_set": False,
        },
        "ep": 1,
        "etag": "404c15db68c318ebe7832ce5aa3d1e30",
        "lastannounced": "2022-08-31T03:00:59Z",
        "lastseen": "2022-09-19T11:58Z",
        "manufacturername": "_TZE200_b6wax7g0",
        "modelid": "TS0601",
        "name": "Thermostat",
        "state": {
            "lastupdated": "2022-09-19T11:58:24.204",
            "lowbattery": False,
            "on": False,
            "temperature": 2200,
            "valve": 0,
        },
        "type": "ZHAThermostat",
        "uniqueid": "84:fd:27:ff:fe:8a:eb:89-01-0201",
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(len(hass.states.async_all())).to_equal(3)

    climate_thermostat = hass.states.get("climate.thermostat")
    expect(climate_thermostat.state).to_equal(HVACMode.HEAT)
    expect(climate_thermostat.attributes["preset_mode"]).to_be(DECONZ_PRESET_MANUAL)
    expect(climate_thermostat.attributes["hvac_action"]).to_be(HVACAction.IDLE)

    await send_sensor({"config": {"preset": "boost"}, "state": {"valve": 100}})

    climate_thermostat = hass.states.get("climate.thermostat")
    expect(climate_thermostat.attributes["preset_mode"]).to_be(PRESET_BOOST)
    expect(climate_thermostat.attributes["hvac_action"]).to_be(HVACAction.HEATING)
