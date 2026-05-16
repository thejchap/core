"""Test qwikswitch sensors."""

import asyncio
from typing import Any
from unittest.mock import Mock

from aiohttp.client_exceptions import ClientError
from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant.components.qwikswitch import DOMAIN
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import qs_devices as qs_devices_fx

from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    caplog as caplog_fx,
    hass as hass_fx,
    hass_storage as hass_storage_fx,
    mock_network,
)
from tests.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
    MockLongPollSideEffect,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


EMPTY_PACKET = {"cmd": ""}


@test
async def binary_sensor_device(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test a binary sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {"name": "s1", "id": "@a00001", "channel": 1, "type": "imod"}
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()

    # verify initial state is off per the 'val' in qs_devices
    state_obj = hass.states.get("binary_sensor.s1")
    expect(state_obj.state).to_equal("off")

    # receive turn on command from network
    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "STATUS.ACK", "data": "4e0e1601", "rssi": "61%"}
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("binary_sensor.s1")
    expect(state_obj.state).to_equal("on")

    # receive turn off command from network
    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "STATUS.ACK", "data": "4e0e1701", "rssi": "61%"},
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("binary_sensor.s1")
    expect(state_obj.state).to_equal("off")

    listen_mock.stop()


@test
async def sensor_device(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test a sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {
                "name": "ss1",
                "id": "@a00001",
                "channel": 1,
                "type": "qwikcord",
            }
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()

    state_obj = hass.states.get("sensor.ss1")
    expect(state_obj.state).to_equal(STATE_UNKNOWN)

    # receive command that sets the sensor value
    listen_mock.queue_response(
        json={"id": "@a00001", "name": "ss1", "type": "rel", "val": "4733800001a00000"},
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("sensor.ss1")
    expect(state_obj.state).to_equal("416")

    listen_mock.stop()


@test
async def switch_device(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test a switch device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"switches": ["@a00001"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()

    # verify initial state is off per the 'val' in qs_devices
    state_obj = hass.states.get("switch.switch_1")
    expect(state_obj.state).to_equal("off")

    # ask hass to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=100", json={"data": "OK"})
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await asyncio.sleep(0.01)
    expect(
        (
            "GET",
            URL("http://127.0.0.1:2020/@a00001=100"),
            None,
            None,
        )
        in aioclient_mock.mock_calls
    ).to_be_truthy()
    # verify state is on
    state_obj = hass.states.get("switch.switch_1")
    expect(state_obj.state).to_equal("on")

    # ask hass to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=0", json={"data": "OK"})
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await hass.async_block_till_done()
    expect(
        (
            "GET",
            URL("http://127.0.0.1:2020/@a00001=0"),
            None,
            None,
        )
        in aioclient_mock.mock_calls
    ).to_be_truthy()
    # verify state is off
    state_obj = hass.states.get("switch.switch_1")
    expect(state_obj.state).to_equal("off")

    # check if setting the value in the network show in hass
    qs_devices[0]["val"] = "ON"
    listen_mock.queue_response(json=EMPTY_PACKET)
    await hass.async_block_till_done()
    state_obj = hass.states.get("switch.switch_1")
    expect(state_obj.state).to_equal("on")

    listen_mock.stop()


@test
async def light_device(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test a light device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()

    # verify initial state is on per the 'val' in qs_devices
    state_obj = hass.states.get("light.dim_3")
    expect(state_obj.state).to_equal("on")
    expect(state_obj.attributes["brightness"]).to_equal(255)

    # ask hass to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=0", json={"data": "OK"})
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.dim_3"}, blocking=True
    )
    await asyncio.sleep(0.01)
    expect(
        (
            "GET",
            URL("http://127.0.0.1:2020/@a00003=0"),
            None,
            None,
        )
        in aioclient_mock.mock_calls
    ).to_be_truthy()
    state_obj = hass.states.get("light.dim_3")
    expect(state_obj.state).to_equal("off")

    # change brightness in network and check that hass updates
    qs_devices[2]["val"] = "280c55"  # half dimmed
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    expect(state_obj.state).to_equal("on")
    expect(16 < state_obj.attributes["brightness"] < 240).to_be_truthy()

    # turn off in the network and see that it is off in hass as well
    qs_devices[2]["val"] = "280c78"  # off
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    expect(state_obj.state).to_equal("off")

    # ask hass to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=100", json={"data": "OK"})
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.dim_3"}, blocking=True
    )
    await hass.async_block_till_done()
    expect(
        (
            "GET",
            URL("http://127.0.0.1:2020/@a00003=100"),
            None,
            None,
        )
        in aioclient_mock.mock_calls
    ).to_be_truthy()
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    expect(state_obj.state).to_equal("on")

    listen_mock.stop()


@test
async def button(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test that buttons fire an event."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"button_events": "TOGGLE"}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()

    button_pressed = Mock()
    hass.bus.async_listen_once("qwikswitch.button.@a00002", button_pressed)
    listen_mock.queue_response(
        json={"id": "@a00002", "cmd": "TOGGLE"},
    )
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    button_pressed.assert_called_once()

    listen_mock.stop()


@test
async def failed_update_devices(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test that code behaves correctly when unable to get the devices."""

    config = {"qwikswitch": {}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", exc=ClientError())
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_falsy()
    await hass.async_start()
    await hass.async_block_till_done()
    listen_mock.stop()


@test
async def single_invalid_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
) -> None:
    """Test that a single misconfigured sensor doesn't block the others."""

    config = {
        "qwikswitch": {
            "sensors": [
                {"name": "ss1", "id": "@a00001", "channel": 1, "type": "qwikcord"},
                {"name": "ss2", "id": "@a00002", "channel": 1, "type": "ERROR_TYPE"},
                {"name": "ss3", "id": "@a00003", "channel": 1, "type": "qwikcord"},
            ]
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()
    await asyncio.sleep(0.01)
    expect(hass.states.get("sensor.ss1")).to_be_truthy()
    expect(hass.states.get("sensor.ss2")).to_be_falsy()
    expect(hass.states.get("sensor.ss3")).to_be_truthy()
    listen_mock.stop()


@test
async def non_binary_sensor_with_binary_args(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
    caplog: Any = Depends(caplog_fx),
) -> None:
    """Test that the system logs a warning when a non-binary device has binary specific args."""

    config = {
        "qwikswitch": {
            "sensors": [
                {
                    "name": "ss1",
                    "id": "@a00001",
                    "channel": 1,
                    "type": "qwikcord",
                    "invert": True,
                },
            ]
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    expect(hass.states.get("sensor.ss1")).to_be_truthy()
    expect("invert should only be used for binary_sensors" in caplog.text).to_be_truthy()
    listen_mock.stop()


@test
async def non_relay_switch(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
    caplog: Any = Depends(caplog_fx),
) -> None:
    """Test logs a warning when a switch is configured for a device that is not a relay."""

    config = {"qwikswitch": {"switches": ["@a00003"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    expect(hass.states.get("switch.dim_3")).to_be_falsy()
    expect(
        "You specified a switch that is not a relay @a00003" in caplog.text
    ).to_be_truthy()
    listen_mock.stop()


@test
async def unknown_device(
    hass: HomeAssistant = Depends(hass_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    qs_devices: list[dict[str, str]] = Depends(qs_devices_fx),
    caplog: Any = Depends(caplog_fx),
) -> None:
    """Test that the system logs a warning when a network device has unknown type."""

    config = {"qwikswitch": {}}
    qs_devices[1]["type"] = "ERROR_TYPE"
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    expect(hass.states.get("light.switch_1")).to_be_truthy()
    expect(hass.states.get("light.light_2")).to_be_falsy()
    expect(hass.states.get("light.dim_3")).to_be_truthy()
    expect("Ignored unknown QSUSB device" in caplog.text).to_be_truthy()
    listen_mock.stop()


@test
async def no_discover_info(
    hass: HomeAssistant = Depends(hass_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    caplog: Any = Depends(caplog_fx),
) -> None:
    """Test that discovery with no discovery_info does not result in errors."""
    config = {
        "qwikswitch": {},
        "light": {"platform": "qwikswitch"},
        "switch": {"platform": "qwikswitch"},
        "sensor": {"platform": "qwikswitch"},
        "binary_sensor": {"platform": "qwikswitch"},
    }
    aioclient_mock.get(
        "http://127.0.0.1:2020/&device",
        json=[
            {
                "id": "@a00001",
                "name": "Switch 1",
                "type": "ERROR_TYPE",
                "val": "OFF",
                "time": "1522777506",
                "rssi": "51%",
            },
        ],
    )
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    expect(await async_setup_component(hass, "light", config)).to_be_truthy()
    expect(await async_setup_component(hass, "switch", config)).to_be_truthy()
    expect(await async_setup_component(hass, "sensor", config)).to_be_truthy()
    expect(await async_setup_component(hass, "binary_sensor", config)).to_be_truthy()
    await hass.async_start()
    await hass.async_block_till_done()
    expect("Error while setting up qwikswitch platform" not in caplog.text).to_be_truthy()
    listen_mock.stop()
