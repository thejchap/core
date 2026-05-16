"""Test the Insteon properties APIs."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, patch

from pyinsteon.config import MOMENTARY_DELAY, RELAY_MODE, TOGGLE_BUTTON
from pyinsteon.config.extended_property import ExtendedProperty
from pyinsteon.constants import RelayMode, ToggleMode
from tryke import Depends, expect, fixture, test

from homeassistant.components import insteon
from homeassistant.components.insteon.api import async_load_api
from homeassistant.components.insteon.api.device import INSTEON_DEVICE_NOT_FOUND
from homeassistant.components.insteon.api.properties import (
    DEVICE_ADDRESS,
    ID,
    PROPERTY_NAME,
    PROPERTY_VALUE,
    RADIO_BUTTON_GROUPS,
    RAMP_RATE_IN_SEC,
    SHOW_ADVANCED,
    TYPE,
)
from homeassistant.core import HomeAssistant

from .mock_devices import MockDevices

from tests.common import load_fixture
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.typing import MockHAClientWebSocket, WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level fixture anchor."""
    return 0


@fixture
def kpl_properties_data() -> dict[str, Any]:
    """Load the controller state fixture data."""
    return json.loads(load_fixture("insteon/kpl_properties.json"))


@fixture
def iolinc_properties_data() -> dict[str, Any]:
    """Load the controller state fixture data."""
    return json.loads(load_fixture("insteon/iolinc_properties.json"))


async def _setup(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    address: str,
    properties_data: dict[str, Any],
) -> tuple[MockHAClientWebSocket, MockDevices]:
    """Set up tests."""
    ws_client = await hass_ws_client(hass)
    devices = MockDevices()
    await devices.async_load()
    devices.fill_properties(address, properties_data)
    async_load_api(hass)
    return ws_client, devices


@test
async def get_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
    iolinc_properties_data: dict[str, Any] = Depends(iolinc_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )
    devices.fill_properties("44.44.44", iolinc_properties_data)

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "33.33.33",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(18)

        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(6)

        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "33.33.33",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(69)

        await ws_client.send_json(
            {
                ID: 5,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(14)


@test
async def get_read_only_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    iolinc_properties_data: dict[str, Any] = Depends(iolinc_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    mock_read_only = ExtendedProperty(
        "44.44.44", "mock_read_only", bool, is_read_only=True
    )
    mock_read_only.set_value(False)

    ws_client, devices = await _setup(
        hass, hass_ws_client, "44.44.44", iolinc_properties_data
    )
    device = devices["44.44.44"]
    device.configuration["mock_read_only"] = mock_read_only
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(6)
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(15)
    await asyncio.sleep(1)


@test
async def get_unknown_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    iolinc_properties_data: dict[str, Any] = Depends(iolinc_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""

    class UnknownType:
        """Mock unknown data type."""

    mock_unknown = ExtendedProperty("44.44.44", "mock_unknown", UnknownType)

    ws_client, devices = await _setup(
        hass, hass_ws_client, "44.44.44", iolinc_properties_data
    )
    device = devices["44.44.44"]
    device.configuration["mock_unknown"] = mock_unknown
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(6)
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(len(msg["result"]["properties"])).to_equal(14)


@test
async def change_bool_property(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test changing a bool type properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: "led_off",
                PROPERTY_VALUE: True,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(devices["33.33.33"].operating_flags["led_off"].is_dirty).to_be(True)


@test
async def change_int_property(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test changing a int type properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: "led_dimming",
                PROPERTY_VALUE: 100,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(devices["33.33.33"].properties["led_dimming"].new_value).to_equal(100)
        expect(devices["33.33.33"].properties["led_dimming"].is_dirty).to_be(True)


@test
async def change_ramp_rate_property(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test changing an Insteon device's ramp rate properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: RAMP_RATE_IN_SEC,
                PROPERTY_VALUE: 4.5,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(devices["33.33.33"].properties["ramp_rate"].new_value).to_equal(0x1A)
        expect(devices["33.33.33"].properties["ramp_rate"].is_dirty).to_be(True)


@test
async def change_radio_button_group(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test changing an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )
    rb_groups = devices["33.33.33"].configuration[RADIO_BUTTON_GROUPS]

    expect(rb_groups.value[0]).to_equal([4, 5])
    expect(rb_groups.value[1]).to_equal([7, 8])

    new_groups_1 = [[1, 4, 5], [7, 8]]
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: RADIO_BUTTON_GROUPS,
                PROPERTY_VALUE: new_groups_1,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(rb_groups.new_value[0]).to_equal([1, 4, 5])
        expect(rb_groups.new_value[1]).to_equal([7, 8])

        new_groups_2 = [[1, 4], [7, 8]]
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: RADIO_BUTTON_GROUPS,
                PROPERTY_VALUE: new_groups_2,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(rb_groups.new_value[0]).to_equal([1, 4])
        expect(rb_groups.new_value[1]).to_equal([7, 8])


@test
async def change_toggle_property(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Update a button's toggle mode."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )
    device = devices["33.33.33"]
    prop_name = f"{TOGGLE_BUTTON}_c"
    toggle_prop = device.configuration[prop_name]
    expect(toggle_prop.value).to_equal(ToggleMode.TOGGLE)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: prop_name,
                PROPERTY_VALUE: str(ToggleMode.ON_ONLY).lower(),
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(toggle_prop.new_value).to_equal(ToggleMode.ON_ONLY)


@test
async def change_relay_mode(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    iolinc_properties_data: dict[str, Any] = Depends(iolinc_properties_data),
) -> None:
    """Update a device's relay mode."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "44.44.44", iolinc_properties_data
    )
    device = devices["44.44.44"]
    relay_prop = device.configuration[RELAY_MODE]
    expect(relay_prop.value).to_equal(RelayMode.MOMENTARY_A)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "44.44.44",
                PROPERTY_NAME: RELAY_MODE,
                PROPERTY_VALUE: str(RelayMode.LATCHING).lower(),
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(relay_prop.new_value).to_equal(RelayMode.LATCHING)


@test
async def change_float_property(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    iolinc_properties_data: dict[str, Any] = Depends(iolinc_properties_data),
) -> None:
    """Update a float type property."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "44.44.44", iolinc_properties_data
    )
    device = devices["44.44.44"]
    delay_prop = device.configuration[MOMENTARY_DELAY]
    delay_prop.set_value(0)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "44.44.44",
                PROPERTY_NAME: MOMENTARY_DELAY,
                PROPERTY_VALUE: 1.8,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)

        expect(delay_prop.new_value).to_equal(1.8)


@test
async def write_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/properties/write", DEVICE_ADDRESS: "33.33.33"}
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(devices["33.33.33"].async_write_op_flags.call_count).to_equal(1)
        expect(devices["33.33.33"].async_write_ext_properties.call_count).to_equal(1)


@test
async def write_properties_failure(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/properties/write", DEVICE_ADDRESS: "22.22.22"}
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(False)
        expect(msg["error"]["code"]).to_equal("write_failed")


@test
async def load_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    device = devices["33.33.33"]
    device.async_read_config = AsyncMock(return_value=1)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/properties/load", DEVICE_ADDRESS: "33.33.33"}
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(devices["33.33.33"].async_read_config.call_count).to_equal(1)


@test
async def load_properties_failure(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    device = devices["33.33.33"]
    device.async_read_config = AsyncMock(return_value=0)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/properties/load", DEVICE_ADDRESS: "33.33.33"}
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(False)
        expect(msg["error"]["code"]).to_equal("load_failed")


@test
async def reset_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    device = devices["33.33.33"]
    device.configuration["led_off"].new_value = True
    device.properties["on_mask"].new_value = 100
    expect(device.operating_flags["led_off"].is_dirty).to_be(True)
    expect(device.properties["on_mask"].is_dirty).to_be(True)
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/properties/reset", DEVICE_ADDRESS: "33.33.33"}
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(True)
        expect(device.operating_flags["led_off"].is_dirty).to_be(False)
        expect(device.properties["on_mask"].is_dirty).to_be(False)


@test
async def bad_address(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    kpl_properties_data: dict[str, Any] = Depends(kpl_properties_data),
) -> None:
    """Test for a bad Insteon address."""
    ws_client, _devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )

    ws_id = 0
    for call in ("get", "write", "load", "reset"):
        ws_id += 1
        params: dict[str, Any] = {
            ID: ws_id,
            TYPE: f"insteon/properties/{call}",
            DEVICE_ADDRESS: "99.99.99",
        }
        if call == "get":
            params[SHOW_ADVANCED] = False
        await ws_client.send_json(params)
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be(False)
        expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)

    ws_id += 1
    await ws_client.send_json(
        {
            ID: ws_id,
            TYPE: "insteon/properties/change",
            DEVICE_ADDRESS: "99.99.99",
            PROPERTY_NAME: "led_off",
            PROPERTY_VALUE: True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)
