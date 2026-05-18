"""The tests for deCONZ logbook (tryke port)."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import CONF_GESTURE, DOMAIN
from homeassistant.components.deconz.deconz_event import (
    CONF_DECONZ_ALARM_EVENT,
    CONF_DECONZ_EVENT,
)
from homeassistant.components.deconz.util import serial_from_unique_id
from homeassistant.const import (
    CONF_CODE,
    CONF_DEVICE_ID,
    CONF_EVENT,
    CONF_ID,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from homeassistant.util import slugify

from tests.components.deconz._fixtures import setup_deconz
from tests.components.logbook.common import MockRow, mock_humanify
from tests.hass_fixtures import (
    aioclient_mock,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test
async def humanifying_deconz_alarm_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test humanifying deCONZ alarm event."""
    sensor_payload: dict[str, Any] = {
        "config": {
            "armed": "disarmed",
            "enrolled": 0,
            "on": True,
            "panel": "disarmed",
            "pending": [],
            "reachable": True,
        },
        "ep": 1,
        "etag": "3c4008d74035dfaa1f0bb30d24468b12",
        "lastseen": "2021-04-02T13:07Z",
        "manufacturername": "Universal Electronics Inc",
        "modelid": "URC4450BC0-X-R",
        "name": "Keypad",
        "state": {
            "action": "armed_away,1111,55",
            "lastupdated": "2021-04-02T13:08:18.937",
            "lowbattery": False,
            "tampered": True,
        },
        "type": "ZHAAncillaryControl",
        "uniqueid": "00:0d:6f:00:13:4f:61:39-01-0501",
    }

    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    keypad_event_id = slugify(sensor_payload["name"])
    keypad_serial = serial_from_unique_id(sensor_payload["uniqueid"])
    keypad_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, keypad_serial)}
    )

    removed_device_event_id = "removed_device"
    removed_device_serial = "00:00:00:00:00:00:00:05"

    hass.config.components.add("recorder")
    expect(await async_setup_component(hass, "logbook", {})).to_be_truthy()
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            MockRow(
                CONF_DECONZ_ALARM_EVENT,
                {
                    CONF_CODE: 1234,
                    CONF_DEVICE_ID: keypad_entry.id,
                    CONF_EVENT: "armed_away",
                    CONF_ID: keypad_event_id,
                    CONF_UNIQUE_ID: keypad_serial,
                },
            ),
            # Event of a removed device
            MockRow(
                CONF_DECONZ_ALARM_EVENT,
                {
                    CONF_CODE: 1234,
                    CONF_DEVICE_ID: "ff99ff99ff99ff99ff99ff99ff99ff99",
                    CONF_EVENT: "armed_away",
                    CONF_ID: removed_device_event_id,
                    CONF_UNIQUE_ID: removed_device_serial,
                },
            ),
        ],
    )

    expect(events[0]["name"]).to_equal("Keypad")
    expect(events[0]["domain"]).to_equal("deconz")
    expect(events[0]["message"]).to_equal("fired event 'armed_away'")

    expect(events[1]["name"]).to_equal("removed_device")
    expect(events[1]["domain"]).to_equal("deconz")
    expect(events[1]["message"]).to_equal("fired event 'armed_away'")


@test
async def humanifying_deconz_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test humanifying deCONZ event."""
    sensor_payload: dict[str, Any] = {
        "1": {
            "name": "Switch 1",
            "type": "ZHASwitch",
            "state": {"buttonevent": 1000},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        "2": {
            "name": "Hue remote",
            "type": "ZHASwitch",
            "modelid": "RWL021",
            "state": {"buttonevent": 1000},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:02-00",
        },
        "3": {
            "name": "Xiaomi cube",
            "type": "ZHASwitch",
            "modelid": "lumi.sensor_cube",
            "state": {"buttonevent": 1000, "gesture": 1},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:03-00",
        },
        "4": {
            "name": "Faulty event",
            "type": "ZHASwitch",
            "state": {},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:04-00",
        },
    }

    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    switch_event_id = slugify(sensor_payload["1"]["name"])
    switch_serial = serial_from_unique_id(sensor_payload["1"]["uniqueid"])
    switch_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, switch_serial)}
    )

    hue_remote_event_id = slugify(sensor_payload["2"]["name"])
    hue_remote_serial = serial_from_unique_id(sensor_payload["2"]["uniqueid"])
    hue_remote_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, hue_remote_serial)}
    )

    xiaomi_cube_event_id = slugify(sensor_payload["3"]["name"])
    xiaomi_cube_serial = serial_from_unique_id(sensor_payload["3"]["uniqueid"])
    xiaomi_cube_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, xiaomi_cube_serial)}
    )

    faulty_event_id = slugify(sensor_payload["4"]["name"])
    faulty_serial = serial_from_unique_id(sensor_payload["4"]["uniqueid"])
    faulty_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, faulty_serial)}
    )

    removed_device_event_id = "removed_device"
    removed_device_serial = "00:00:00:00:00:00:00:05"

    hass.config.components.add("recorder")
    expect(await async_setup_component(hass, "logbook", {})).to_be_truthy()
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            # Event without matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: switch_entry.id,
                    CONF_EVENT: 2000,
                    CONF_ID: switch_event_id,
                    CONF_UNIQUE_ID: switch_serial,
                },
            ),
            # Event with matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: hue_remote_entry.id,
                    CONF_EVENT: 2001,
                    CONF_ID: hue_remote_event_id,
                    CONF_UNIQUE_ID: hue_remote_serial,
                },
            ),
            # Gesture with matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: xiaomi_cube_entry.id,
                    CONF_GESTURE: 1,
                    CONF_ID: xiaomi_cube_event_id,
                    CONF_UNIQUE_ID: xiaomi_cube_serial,
                },
            ),
            # Unsupported device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: xiaomi_cube_entry.id,
                    CONF_GESTURE: "unsupported_gesture",
                    CONF_ID: xiaomi_cube_event_id,
                    CONF_UNIQUE_ID: xiaomi_cube_serial,
                },
            ),
            # Unknown event
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: faulty_entry.id,
                    "unknown_event": None,
                    CONF_ID: faulty_event_id,
                    CONF_UNIQUE_ID: faulty_serial,
                },
            ),
            # Event of a removed device
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: "ff99ff99ff99ff99ff99ff99ff99ff99",
                    CONF_EVENT: 2000,
                    CONF_ID: removed_device_event_id,
                    CONF_UNIQUE_ID: removed_device_serial,
                },
            ),
        ],
    )

    expect(events[0]["name"]).to_equal("Switch 1")
    expect(events[0]["domain"]).to_equal("deconz")
    expect(events[0]["message"]).to_equal("fired event '2000'")

    expect(events[1]["name"]).to_equal("Hue remote")
    expect(events[1]["domain"]).to_equal("deconz")
    expect(events[1]["message"]).to_equal("'Long press' event for 'Dim up' was fired")

    expect(events[2]["name"]).to_equal("Xiaomi cube")
    expect(events[2]["domain"]).to_equal("deconz")
    expect(events[2]["message"]).to_equal("fired event 'Shake'")

    expect(events[3]["name"]).to_equal("Xiaomi cube")
    expect(events[3]["domain"]).to_equal("deconz")
    expect(events[3]["message"]).to_equal("fired event 'unsupported_gesture'")

    expect(events[4]["name"]).to_equal("Faulty event")
    expect(events[4]["domain"]).to_equal("deconz")
    expect(events[4]["message"]).to_equal("fired an unknown event")

    expect(events[5]["name"]).to_equal("removed_device")
    expect(events[5]["domain"]).to_equal("deconz")
    expect(events[5]["message"]).to_equal("fired event '2000'")
