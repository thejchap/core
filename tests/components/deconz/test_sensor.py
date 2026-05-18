"""deCONZ sensor platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import CONF_ALLOW_CLIP_SENSOR
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
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


@test.skip("snapshot test - parametrize id mismatch with pytest snapshots")
async def sensors() -> None:
    """Snapshot-based parametrize test cannot reuse pytest .ambr ids."""


@test
async def not_allow_clip_sensor(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that CLIP sensors are not allowed."""
    sensor_payload = {
        "name": "CLIP temperature sensor",
        "type": "CLIPTemperature",
        "state": {"temperature": 2600},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    }
    await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_CLIP_SENSOR: False},
        sensor_payload=sensor_payload,
    )
    expect(len(hass.states.async_all())).to_be(0)


@test
async def allow_clip_sensors(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that CLIP sensors can be allowed."""
    sensor_payload = {
        "1": {
            "name": "Light level sensor",
            "type": "ZHALightLevel",
            "state": {"lightlevel": 30000, "dark": False},
            "config": {"on": True, "reachable": True, "temperature": 10},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
        "2": {
            "id": "CLIP light sensor id",
            "name": "CLIP light level sensor",
            "type": "CLIPLightLevel",
            "state": {"lightlevel": 30000},
            "config": {"reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        "3": {
            "config": {"on": True, "reachable": True},
            "etag": "a5ed309124d9b7a21ef29fc278f2625e",
            "manufacturername": "Philips",
            "modelid": "CLIPGenericStatus",
            "name": "CLIP Flur",
            "state": {"lastupdated": "2021-10-01T10:23:06.779", "status": 0},
            "swversion": "1.0",
            "type": "CLIPGenericStatus",
            "uniqueid": "/sensors/3",
        },
    }
    config_entry = await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_CLIP_SENSOR: True},
        sensor_payload=sensor_payload,
    )

    # Disallow clip sensors
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: False}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(2)
    expect(hass.states.get("sensor.clip_light_level_sensor")).to_be(None)
    expect(hass.states.get("sensor.clip_flur")).to_be(None)

    # Allow clip sensors
    hass.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: True}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(4)
    expect(hass.states.get("sensor.clip_light_level_sensor").state).to_equal("999.8")
    expect(hass.states.get("sensor.clip_flur").state).to_equal("0")


@test
async def add_new_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that adding a new sensor works."""
    await setup_deconz(hass, aioclient)
    expect(len(hass.states.async_all())).to_be(0)

    event_added_sensor = {
        "e": "added",
        "sensor": {
            "id": "Light sensor id",
            "name": "Light level sensor",
            "type": "ZHALightLevel",
            "state": {"lightlevel": 30000, "dark": False},
            "config": {"on": True, "reachable": True, "temperature": 10},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
    }
    await send_sensor(event_added_sensor)
    expect(len(hass.states.async_all())).to_be(2)
    expect(hass.states.get("sensor.light_level_sensor").state).to_equal("999.8")


@test.cases(
    test.case("consumption", sensor_type="ZHAConsumption", sensor_property="consumption"),
    test.case("humidity", sensor_type="ZHAHumidity", sensor_property="humidity"),
    test.case("lightlevel", sensor_type="ZHALightLevel", sensor_property="lightlevel"),
    test.case("temperature", sensor_type="ZHATemperature", sensor_property="temperature"),
)
async def dont_add_sensor_if_state_is_none(
    sensor_type: str,
    sensor_property: str,
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test sensor with scaled data is not created if state is None."""
    sensor_payload = {
        "0": {
            "name": "Sensor 1",
            "type": sensor_type,
            "state": {sensor_property: None},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        }
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)
    expect(len(hass.states.async_all())).to_be(0)


@test
async def air_quality_sensor_without_ppb(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test sensor with scaled data is not created if state is None."""
    sensor_payload = {
        "config": {
            "on": True,
            "reachable": True,
        },
        "ep": 2,
        "etag": "c2d2e42396f7c78e11e46c66e2ec0200",
        "lastseen": "2020-11-20T22:48Z",
        "manufacturername": "BOSCH",
        "modelid": "AIR",
        "name": "BOSCH Air quality sensor",
        "state": {
            "airquality": "poor",
            "lastupdated": "2020-11-20T22:48:00.209",
        },
        "swversion": "20200402",
        "type": "ZHAAirQuality",
        "uniqueid": "00:00:00:00:00:00:00:00-02-fdef",
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)
    expect(len(hass.states.async_all())).to_be(1)


@test
async def add_battery_later(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that a battery sensor can be created later on."""
    sensor_payload = {
        "1": {
            "name": "Switch 1",
            "type": "ZHASwitch",
            "state": {"buttonevent": 1000},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:00-00-0000",
        },
        "2": {
            "name": "Switch 2",
            "type": "ZHASwitch",
            "state": {"buttonevent": 1000},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:00-00-0001",
        },
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(len(hass.states.async_all())).to_be(0)

    await send_sensor({"id": "2", "config": {"battery": 50}})
    expect(len(hass.states.async_all())).to_be(0)

    await send_sensor({"id": "1", "config": {"battery": 50}})
    expect(len(hass.states.async_all())).to_be(1)
    expect(hass.states.get("sensor.switch_1_battery").state).to_equal("50")


def _danfoss_payload(model_id: str) -> dict[str, Any]:
    """Build the Danfoss multi-endpoint sensor payload."""
    return {
        "1": {
            "config": {
                "battery": 70,
                "heatsetpoint": 2300,
                "offset": 0,
                "on": True,
                "reachable": True,
                "schedule": {},
                "schedule_on": False,
            },
            "ep": 1,
            "etag": "982d9acc38bee5b251e24a9be26558e4",
            "lastseen": "2021-02-15T12:23Z",
            "manufacturername": "Danfoss",
            "modelid": model_id,
            "name": "0x8030",
            "state": {
                "lastupdated": "2021-02-15T12:23:07.994",
                "on": False,
                "temperature": 2307,
            },
            "swversion": "YYYYMMDD",
            "type": "ZHAThermostat",
            "uniqueid": "58:8e:81:ff:fe:00:11:22-01-0201",
        },
        "2": {
            "config": {
                "battery": 86,
                "heatsetpoint": 2300,
                "offset": 0,
                "on": True,
                "reachable": True,
                "schedule": {},
                "schedule_on": False,
            },
            "ep": 2,
            "etag": "62f12749f9f51c950086aff37dd02b61",
            "lastseen": "2021-02-15T12:23Z",
            "manufacturername": "Danfoss",
            "modelid": model_id,
            "name": "0x8030",
            "state": {
                "lastupdated": "2021-02-15T12:23:22.399",
                "on": False,
                "temperature": 2316,
            },
            "swversion": "YYYYMMDD",
            "type": "ZHAThermostat",
            "uniqueid": "58:8e:81:ff:fe:00:11:22-02-0201",
        },
        "3": {
            "config": {
                "battery": 86,
                "heatsetpoint": 2350,
                "offset": 0,
                "on": True,
                "reachable": True,
                "schedule": {},
                "schedule_on": False,
            },
            "ep": 3,
            "etag": "f50061174bb7f18a3d95789bab8b646d",
            "lastseen": "2021-02-15T12:23Z",
            "manufacturername": "Danfoss",
            "modelid": model_id,
            "name": "0x8030",
            "state": {
                "lastupdated": "2021-02-15T12:23:25.466",
                "on": False,
                "temperature": 2337,
            },
            "swversion": "YYYYMMDD",
            "type": "ZHAThermostat",
            "uniqueid": "58:8e:81:ff:fe:00:11:22-03-0201",
        },
        "4": {
            "config": {
                "battery": 85,
                "heatsetpoint": 2300,
                "offset": 0,
                "on": True,
                "reachable": True,
                "schedule": {},
                "schedule_on": False,
            },
            "ep": 4,
            "etag": "eea97adf8ce1b971b8b6a3a31793f96b",
            "lastseen": "2021-02-15T12:23Z",
            "manufacturername": "Danfoss",
            "modelid": model_id,
            "name": "0x8030",
            "state": {
                "lastupdated": "2021-02-15T12:23:41.939",
                "on": False,
                "temperature": 2333,
            },
            "swversion": "YYYYMMDD",
            "type": "ZHAThermostat",
            "uniqueid": "58:8e:81:ff:fe:00:11:22-04-0201",
        },
        "5": {
            "config": {
                "battery": 83,
                "heatsetpoint": 2300,
                "offset": 0,
                "on": True,
                "reachable": True,
                "schedule": {},
                "schedule_on": False,
            },
            "ep": 5,
            "etag": "1f7cd1a5d66dc27ac5eb44b8c47362fb",
            "lastseen": "2021-02-15T12:23Z",
            "manufacturername": "Danfoss",
            "modelid": model_id,
            "name": "0x8030",
            "state": {"lastupdated": "none", "on": False, "temperature": 2325},
            "swversion": "YYYYMMDD",
            "type": "ZHAThermostat",
            "uniqueid": "58:8e:81:ff:fe:00:11:22-05-0201",
        },
    }


@test.cases(
    test.case("0x8030", model_id="0x8030"),
    test.case("0x8031", model_id="0x8031"),
    test.case("0x8034", model_id="0x8034"),
    test.case("0x8035", model_id="0x8035"),
)
async def special_danfoss_battery_creation(
    model_id: str,
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the special Danfoss battery creation works."""
    await setup_deconz(hass, aioclient, sensor_payload=_danfoss_payload(model_id))

    expect(len(hass.states.async_all())).to_be(10)
    expect(len(hass.states.async_entity_ids(SENSOR_DOMAIN))).to_be(5)


@test
async def unsupported_sensor(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that unsupported sensors doesn't break anything."""
    sensor_payload = {"type": "not supported", "name": "name", "state": {}, "config": {}}
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)
    expect(len(hass.states.async_all())).to_be(0)
