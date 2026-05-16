"""Test the device level APIs."""

import asyncio
from unittest.mock import patch

from pyinsteon.constants import DeviceAction
from pyinsteon.topics import DEVICE_LIST_CHANGED
from pyinsteon.utils import publish_topic
from tryke import Depends, expect, fixture, test

from homeassistant.components import insteon
from homeassistant.components.insteon.api import async_load_api
from homeassistant.components.insteon.api.device import (
    DEVICE_ID,
    HA_DEVICE_NOT_FOUND,
    ID,
    INSTEON_DEVICE_NOT_FOUND,
    TYPE,
)
from homeassistant.components.insteon.const import (
    CONF_OVERRIDE,
    CONF_X10,
    DOMAIN,
    MULTIPLE,
)
from homeassistant.components.insteon.utils import async_device_name
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import MOCK_USER_INPUT_PLM
from .mock_devices import MockDevices
from .mock_setup import async_mock_setup

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def get_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting an Insteon device."""

    ws_client, devices, ha_device, _ = await async_mock_setup(hass, hass_ws_client)
    with patch.object(insteon.api.device, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/device/get", DEVICE_ID: ha_device.id}
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

        expect(result["name"]).to_equal("Device 11.11.11")
        expect(result["address"]).to_equal("11.11.11")


@test
async def no_ha_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test response when no HA device exists."""

    ws_client, devices, _, _ = await async_mock_setup(hass, hass_ws_client)
    with patch.object(insteon.api.device, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/device/get", DEVICE_ID: "not_a_device"}
        )
        msg = await ws_client.receive_json()
        expect(msg.get("result")).to_be_falsy()
        expect(msg.get("error")).to_be_truthy()
        expect(msg["error"]["message"]).to_equal(HA_DEVICE_NOT_FOUND)


@test
async def no_insteon_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test response when no Insteon device exists."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="abcde12345",
        data=MOCK_USER_INPUT_PLM,
        options={},
    )
    config_entry.add_to_hass(hass)
    async_load_api(hass)

    ws_client = await hass_ws_client(hass)
    devices = MockDevices()
    await devices.async_load()

    ha_device_1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "AA.BB.CC")},
        name="HA Device Only",
    )
    ha_device_2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("other_domain", "no address")},
        name="HA Device Only",
    )
    with patch.object(insteon.api.device, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/device/get", DEVICE_ID: ha_device_1.id}
        )
        msg = await ws_client.receive_json()
        expect(msg.get("result")).to_be_falsy()
        expect(msg.get("error")).to_be_truthy()
        expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)

        await ws_client.send_json(
            {ID: 3, TYPE: "insteon/device/get", DEVICE_ID: ha_device_2.id}
        )
        msg = await ws_client.receive_json()
        expect(msg.get("result")).to_be_falsy()
        expect(msg.get("error")).to_be_truthy()
        expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)


@test
async def get_ha_device_name(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the HA device name from an Insteon address."""

    _, devices, _, device_reg = await async_mock_setup(hass, hass_ws_client)

    with patch.object(insteon.api.device, "devices", devices):
        name = await async_device_name(device_reg, "11.11.11")
        expect(name).to_equal("Device 11.11.11")

        name = await async_device_name(device_reg, "BB.BB.BB")
        expect(name).to_equal("")


@test
async def add_device_api(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding an Insteon device."""

    ws_client, devices, _, _ = await async_mock_setup(hass, hass_ws_client)
    with patch.object(insteon.api.device, "devices", devices):
        await ws_client.send_json({ID: 2, TYPE: "insteon/device/add", MULTIPLE: True})

        await asyncio.sleep(0.01)
        expect(devices.async_add_device_called_with.get("address")).to_be(None)
        expect(devices.async_add_device_called_with["multiple"]).to_be(True)

        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("device_added")
        expect(msg["event"]["address"]).to_equal("aa.bb.cc")

        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("device_added")
        expect(msg["event"]["address"]).to_equal("bb.cc.dd")

        publish_topic(
            DEVICE_LIST_CHANGED,
            address=None,
            action=DeviceAction.COMPLETED,
        )
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("linking_stopped")


@test
async def cancel_add_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test cancelling adding of a new device."""

    ws_client, devices, _, _ = await async_mock_setup(hass, hass_ws_client)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/device/add/cancel",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()


@test
async def add_x10_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding an X10 device."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    x10_device = {"housecode": "a", "unitcode": 1, "platform": "switch"}
    await ws_client.send_json(
        {ID: 2, TYPE: "insteon/device/add_x10", "x10_device": x10_device}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_X10])).to_equal(1)
    expect(config_entry.options[CONF_X10][0]["housecode"]).to_equal("a")
    expect(config_entry.options[CONF_X10][0]["unitcode"]).to_equal(1)
    expect(config_entry.options[CONF_X10][0]["platform"]).to_equal("switch")


@test
async def add_x10_device_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding a duplicate X10 device."""

    x10_device = {"housecode": "a", "unitcode": 1, "platform": "switch"}

    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options={CONF_X10: [x10_device]}
    )
    await ws_client.send_json(
        {ID: 2, TYPE: "insteon/device/add_x10", "x10_device": x10_device}
    )
    msg = await ws_client.receive_json()
    expect(msg["error"]).to_be_truthy()
    expect(msg["error"]["code"]).to_equal("duplicate")


@test
async def remove_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing an Insteon device."""
    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/device/remove",
            "device_address": "11.22.33",
            "remove_all_refs": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()


@test
async def remove_x10_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing an X10 device."""
    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/device/remove",
            "device_address": "X10.A.01",
            "remove_all_refs": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()


@test
async def remove_one_x10_device(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test one X10 device without removing others."""
    x10_device = {"housecode": "a", "unitcode": 1, "platform": "light", "dim_steps": 22}
    x10_devices = [
        x10_device,
        {"housecode": "a", "unitcode": 2, "platform": "switch"},
    ]
    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options={CONF_X10: x10_devices}
    )
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/device/remove",
            "device_address": "X10.A.01",
            "remove_all_refs": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()
    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_X10])).to_equal(1)
    expect(config_entry.options[CONF_X10][0]["housecode"]).to_equal("a")
    expect(config_entry.options[CONF_X10][0]["unitcode"]).to_equal(2)


@test
async def remove_device_with_overload(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing an Insteon device that has a device overload."""
    overload = {"address": "99.99.99", "cat": 1, "subcat": 3}
    overloads = {CONF_OVERRIDE: [overload]}
    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options=overloads
    )
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/device/remove",
            "device_address": "99.99.99",
            "remove_all_refs": True,
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(config_entry.options.get(CONF_OVERRIDE)).to_be_falsy()
