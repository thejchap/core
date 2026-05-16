"""Test the Insteon APIs for configuring the integration."""

import asyncio
import json
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import insteon
from homeassistant.components.insteon.api.device import ID, TYPE
from homeassistant.components.insteon.const import (
    CONF_HUB_VERSION,
    CONF_OVERRIDE,
    CONF_X10,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from .const import (
    MOCK_DEVICE,
    MOCK_HOSTNAME,
    MOCK_USER_INPUT_HUB_V1,
    MOCK_USER_INPUT_HUB_V2,
    MOCK_USER_INPUT_PLM,
)
from .mock_connection import mock_failed_connection, mock_successful_connection
from .mock_devices import MockDevices
from .mock_setup import async_mock_setup

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import WebSocketGenerator


class MockProtocol:
    """A mock Insteon protocol object."""

    connected = True


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def get_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon configuration."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    await ws_client.send_json({ID: 2, TYPE: "insteon/config/get"})
    msg = await ws_client.receive_json()
    result = msg["result"]

    expect(result["modem_config"]).to_equal({"device": MOCK_DEVICE})


@test
async def get_modem_schema_plm(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon PLM modem configuration schema."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    await ws_client.send_json({ID: 2, TYPE: "insteon/config/get_modem_schema"})
    msg = await ws_client.receive_json()
    result = msg["result"][0]

    expect(result["default"]).to_equal(MOCK_DEVICE)
    expect(result["name"]).to_equal("device")
    expect(result["required"]).to_be_truthy()


@test
async def get_modem_schema_hub(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon PLM modem configuration schema."""

    ws_client, _devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
        config_data={**MOCK_USER_INPUT_HUB_V2, CONF_HUB_VERSION: 2},
    )
    await ws_client.send_json({ID: 2, TYPE: "insteon/config/get_modem_schema"})
    msg = await ws_client.receive_json()
    result = msg["result"][0]

    expect(result["default"]).to_equal(MOCK_HOSTNAME)
    expect(result["name"]).to_equal("host")
    expect(result["required"]).to_be_truthy()


@test
async def update_modem_config_plm(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon PLM modem configuration schema."""

    ws_client, mock_devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
    )
    with (
        patch(
            "homeassistant.components.insteon.api.config.async_connect",
            new=mock_successful_connection,
        ),
        patch("homeassistant.components.insteon.api.config.devices", mock_devices),
        patch("homeassistant.components.insteon.api.config.async_close"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/config/update_modem_config",
                "config": MOCK_USER_INPUT_PLM,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

        expect(result["status"]).to_equal("success")


@test
async def update_modem_config_hub_v2(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon HubV2 modem configuration schema."""

    ws_client, mock_devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
        config_data={**MOCK_USER_INPUT_HUB_V2, CONF_HUB_VERSION: 2},
        config_options={"dev_path": "/some/path"},
    )
    with (
        patch(
            "homeassistant.components.insteon.api.config.async_connect",
            new=mock_successful_connection,
        ),
        patch("homeassistant.components.insteon.api.config.devices", mock_devices),
        patch("homeassistant.components.insteon.api.config.async_close"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/config/update_modem_config",
                "config": MOCK_USER_INPUT_HUB_V2,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

        expect(result["status"]).to_equal("success")


@test
async def update_modem_config_hub_v1(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting the Insteon HubV1 modem configuration schema."""

    ws_client, mock_devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
        config_data={**MOCK_USER_INPUT_HUB_V1, CONF_HUB_VERSION: 1},
    )
    with (
        patch(
            "homeassistant.components.insteon.api.config.async_connect",
            new=mock_successful_connection,
        ),
        patch("homeassistant.components.insteon.api.config.devices", mock_devices),
        patch("homeassistant.components.insteon.api.config.async_close"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/config/update_modem_config",
                "config": MOCK_USER_INPUT_HUB_V1,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

        expect(result["status"]).to_equal("success")


@test
async def update_modem_config_bad(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test updating the Insteon modem configuration with bad connection information."""

    ws_client, mock_devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
    )
    with (
        patch(
            "homeassistant.components.insteon.api.config.async_connect",
            new=mock_failed_connection,
        ),
        patch("homeassistant.components.insteon.api.config.devices", mock_devices),
        patch("homeassistant.components.insteon.api.config.async_close"),
    ):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/config/update_modem_config",
                "config": MOCK_USER_INPUT_PLM,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["error"]
        expect(result["code"]).to_equal("connection_failed")


@test
async def update_modem_config_bad_reconnect(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test updating the Insteon modem configuration with bad connection information so reconnect to old."""

    ws_client, mock_devices, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
    )
    with (
        patch(
            "homeassistant.components.insteon.api.config.async_connect",
            new=mock_failed_connection,
        ),
        patch("homeassistant.components.insteon.api.config.devices", mock_devices),
        patch("homeassistant.components.insteon.api.config.async_close"),
    ):
        mock_devices.modem.protocol = MockProtocol()
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/config/update_modem_config",
                "config": MOCK_USER_INPUT_PLM,
            }
        )
        msg = await ws_client.receive_json()
        result = msg["error"]
        expect(result["code"]).to_equal("connection_failed")


@test
async def add_device_override(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding a device configuration override."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    override = {
        "address": "99.99.99",
        "cat": "0x01",
        "subcat": "0x03",
    }
    await ws_client.send_json(
        {ID: 2, TYPE: "insteon/config/device_override/add", "override": override}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_OVERRIDE])).to_equal(1)
    expect(config_entry.options[CONF_OVERRIDE][0]["address"]).to_equal("99.99.99")


@test
async def add_device_override_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding a duplicate device configuration override."""

    override = {
        "address": "99.99.99",
        "cat": "0x01",
        "subcat": "0x03",
    }

    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options={CONF_OVERRIDE: [override]}
    )
    await ws_client.send_json(
        {ID: 2, TYPE: "insteon/config/device_override/add", "override": override}
    )
    msg = await ws_client.receive_json()
    expect(msg["error"]).to_be_truthy()


@test
async def remove_device_override(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing a device configuration override."""

    override = {
        "address": "99.99.99",
        "cat": "0x01",
        "subcat": "0x03",
    }
    overrides = [
        override,
        {
            "address": "88.88.88",
            "cat": "0x02",
            "subcat": "0x05",
        },
    ]

    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options={CONF_OVERRIDE: overrides}
    )
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/config/device_override/remove",
            "device_address": "99.99.99",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_OVERRIDE])).to_equal(1)
    expect(config_entry.options[CONF_OVERRIDE][0]["address"]).to_equal("88.88.88")


@test
async def add_device_override_with_x10(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test adding a device configuration override when X10 configuration exists."""

    x10_device = {"housecode": "a", "unitcode": 1, "platform": "switch"}
    ws_client, _, _, _ = await async_mock_setup(
        hass, hass_ws_client, config_options={CONF_X10: [x10_device]}
    )
    override = {
        "address": "99.99.99",
        "cat": "0x01",
        "subcat": "0x03",
    }
    await ws_client.send_json(
        {ID: 2, TYPE: "insteon/config/device_override/add", "override": override}
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_X10])).to_equal(1)


@test
async def remove_device_override_with_x10(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing a device configuration override when X10 configuration exists."""

    override = {
        "address": "99.99.99",
        "cat": "0x01",
        "subcat": "0x03",
    }
    overrides = [
        override,
        {
            "address": "88.88.88",
            "cat": "0x02",
            "subcat": "0x05",
        },
    ]
    x10_device = {"housecode": "a", "unitcode": 1, "platform": "switch"}

    ws_client, _, _, _ = await async_mock_setup(
        hass,
        hass_ws_client,
        config_options={CONF_OVERRIDE: overrides, CONF_X10: [x10_device]},
    )
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/config/device_override/remove",
            "device_address": "99.99.99",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(len(config_entry.options[CONF_X10])).to_equal(1)


@test
async def remove_device_override_no_overrides(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test removing a device override when no overrides are configured."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    await ws_client.send_json(
        {
            ID: 2,
            TYPE: "insteon/config/device_override/remove",
            "device_address": "99.99.99",
        }
    )
    msg = await ws_client.receive_json()
    expect(msg["success"]).to_be_truthy()

    config_entry = hass.config_entries.async_get_entry("abcde12345")
    expect(config_entry.options.get(CONF_OVERRIDE)).to_be_falsy()


@test
async def get_broken_links(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting broken ALDB links."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    devices = MockDevices()
    await devices.async_load()
    aldb_data = json.loads(await async_load_fixture(hass, "aldb_data.json", DOMAIN))
    devices.fill_aldb("33.33.33", aldb_data)
    await asyncio.sleep(1)
    with patch.object(insteon.api.config, "devices", devices):
        await ws_client.send_json({ID: 2, TYPE: "insteon/config/get_broken_links"})
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()

        expect(len(msg["result"])).to_equal(5)


@test
async def get_unknown_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test getting unknown Insteon devices."""

    ws_client, _, _, _ = await async_mock_setup(hass, hass_ws_client)
    devices = MockDevices()
    await devices.async_load()
    aldb_data = {
        "4095": {
            "memory": 4095,
            "in_use": True,
            "controller": False,
            "high_water_mark": False,
            "bit5": True,
            "bit4": False,
            "group": 0,
            "target": "FFFFFF",
            "data1": 0,
            "data2": 0,
            "data3": 0,
        },
    }
    devices.fill_aldb("33.33.33", aldb_data)
    with patch.object(insteon.api.config, "devices", devices):
        await ws_client.send_json({ID: 2, TYPE: "insteon/config/get_unknown_devices"})
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()

        expect(len(msg["result"])).to_equal(1)
        await asyncio.sleep(0.1)
