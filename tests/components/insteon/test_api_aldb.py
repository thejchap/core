"""Test the Insteon All-Link Database APIs."""

import asyncio
import json
from typing import Any
from unittest.mock import patch

from pyinsteon import pub
from pyinsteon.address import Address
from pyinsteon.constants import ALDBStatus
from pyinsteon.topics import ALDB_LINK_CHANGED, ALDB_STATUS_CHANGED
from tryke import Depends, expect, fixture, test

from homeassistant.components import insteon
from homeassistant.components.insteon.api import async_load_api
from homeassistant.components.insteon.api.aldb import (
    ALDB_RECORD,
    DEVICE_ADDRESS,
    ID,
    TYPE,
)
from homeassistant.components.insteon.api.device import INSTEON_DEVICE_NOT_FOUND
from homeassistant.core import HomeAssistant

from .mock_devices import MockDevices

from tests.common import load_fixture
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import MockHAClientWebSocket, WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    return 0


@fixture
def aldb_data() -> dict[str, Any]:
    """Load the controller state fixture data."""
    return json.loads(load_fixture("insteon/aldb_data.json"))


async def _setup(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, aldb_data: dict[str, Any]
) -> tuple[MockHAClientWebSocket, MockDevices]:
    """Set up tests."""
    ws_client = await hass_ws_client(hass)
    devices = MockDevices()
    await devices.async_load()
    async_load_api(hass)
    devices.fill_aldb("33.33.33", aldb_data)
    return ws_client, devices


def _compare_records(aldb_rec, dict_rec):
    """Compare a record in the ALDB to the dictionary record."""
    expect(aldb_rec.is_in_use).to_equal(dict_rec["in_use"])
    expect(aldb_rec.is_controller).to_equal(dict_rec["is_controller"])
    expect(aldb_rec.is_high_water_mark).to_be_falsy()
    expect(aldb_rec.group).to_equal(dict_rec["group"])
    expect(aldb_rec.target).to_equal(Address(dict_rec["target"]))
    expect(aldb_rec.data1).to_equal(dict_rec["data1"])
    expect(aldb_rec.data2).to_equal(dict_rec["data2"])
    expect(aldb_rec.data3).to_equal(dict_rec["data3"])


def _aldb_dict(mem_addr):
    """Generate an ALDB record as a dictionary."""
    return {
        "mem_addr": mem_addr,
        "in_use": True,
        "is_controller": True,
        "highwater": False,
        "group": 100,
        "target": "111111",
        "data1": 101,
        "data2": 102,
        "data3": 103,
        "dirty": True,
    }


@test
async def get_aldb(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test getting an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {ID: 2, TYPE: "insteon/aldb/get", DEVICE_ADDRESS: "33.33.33"}
        )
        msg = await ws_client.receive_json()
        result = msg["result"]

        expect(len(result)).to_equal(5)


@test
async def change_aldb_record(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test changing an Insteon device's All-Link Database record."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)
    change_rec = _aldb_dict(4079)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/change",
                DEVICE_ADDRESS: "33.33.33",
                ALDB_RECORD: change_rec,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(len(devices["33.33.33"].aldb.pending_changes)).to_equal(1)
        rec = devices["33.33.33"].aldb.pending_changes[4079]
        _compare_records(rec, change_rec)


@test
async def create_aldb_record(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test creating a new Insteon All-Link Database record."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)
    new_rec = _aldb_dict(4079)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/create",
                DEVICE_ADDRESS: "33.33.33",
                ALDB_RECORD: new_rec,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(len(devices["33.33.33"].aldb.pending_changes)).to_equal(1)
        rec = devices["33.33.33"].aldb.pending_changes[-1]
        _compare_records(rec, new_rec)


@test
async def write_aldb(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test writing an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/write",
                DEVICE_ADDRESS: "33.33.33",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(devices["33.33.33"].aldb.async_write.call_count).to_equal(1)
        expect(devices["33.33.33"].aldb.async_load.call_count).to_equal(1)
        expect(devices.async_save.call_count).to_equal(1)


@test
async def load_aldb(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test loading an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/load",
                DEVICE_ADDRESS: "AA.AA.AA",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(devices["AA.AA.AA"].aldb.async_load.call_count).to_equal(1)
        expect(devices.async_save.call_count).to_equal(1)


@test
async def reset_aldb(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test resetting an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)
    record = _aldb_dict(4079)
    devices["33.33.33"].aldb.modify(
        mem_addr=record["mem_addr"],
        in_use=record["in_use"],
        group=record["group"],
        controller=record["is_controller"],
        target=record["target"],
        data1=record["data1"],
        data2=record["data2"],
        data3=record["data3"],
    )

    expect(devices["33.33.33"].aldb.pending_changes).to_be_truthy()
    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/reset",
                DEVICE_ADDRESS: "33.33.33",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(devices["33.33.33"].aldb.pending_changes).to_be_falsy()


@test
async def default_links(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test getting an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/add_default_links",
                DEVICE_ADDRESS: "33.33.33",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()
        expect(devices["33.33.33"].async_add_default_links.call_count).to_equal(1)
        expect(devices["33.33.33"].aldb.async_load.call_count).to_equal(1)
        expect(devices.async_save.call_count).to_equal(1)


@test
async def notify_on_aldb_status(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test getting an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/notify",
                DEVICE_ADDRESS: "33.33.33",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()

        pub.sendMessage(f"333333.{ALDB_STATUS_CHANGED}", status=ALDBStatus.LOADED)
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("status_changed")
        expect(msg["event"]["is_loading"]).to_be_falsy()


@test
async def notify_on_aldb_record_added(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test getting an Insteon device's All-Link Database."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/aldb/notify",
                DEVICE_ADDRESS: "33.33.33",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()

        pub.sendMessage(
            f"333333.{ALDB_LINK_CHANGED}",
            record="some record",
            sender=Address("11.11.11"),
            deleted=False,
        )
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("record_loaded")


@test
async def bad_address(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test for a bad Insteon address."""
    ws_client, _ = await _setup(hass, hass_ws_client, aldb_data)
    record = _aldb_dict(0)

    ws_id = 0
    for call in ("get", "write", "load", "reset", "add_default_links", "notify"):
        ws_id += 1
        await ws_client.send_json(
            {
                ID: ws_id,
                TYPE: f"insteon/aldb/{call}",
                DEVICE_ADDRESS: "99.99.99",
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_falsy()
        expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)

    for call in ("change", "create"):
        ws_id += 1
        await ws_client.send_json(
            {
                ID: ws_id,
                TYPE: f"insteon/aldb/{call}",
                DEVICE_ADDRESS: "99.99.99",
                ALDB_RECORD: record,
            }
        )
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_falsy()
        expect(msg["error"]["message"]).to_equal(INSTEON_DEVICE_NOT_FOUND)


@test
async def notify_on_aldb_loading(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    aldb_data: dict[str, Any] = Depends(aldb_data),
) -> None:
    """Test tracking changes to ALDB status across all devices."""
    ws_client, devices = await _setup(hass, hass_ws_client, aldb_data)

    with patch.object(insteon.api.aldb, "devices", devices):
        await ws_client.send_json_auto_id({TYPE: "insteon/aldb/notify_all"})
        msg = await ws_client.receive_json()
        expect(msg["success"]).to_be_truthy()

        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("status")
        expect(msg["event"]["is_loading"]).to_be_falsy()

        device = devices["333333"]
        device.aldb._update_status(ALDBStatus.LOADING)
        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("status")
        expect(msg["event"]["is_loading"]).to_be_truthy()

        device.aldb._update_status(ALDBStatus.LOADED)
        await asyncio.sleep(0.1)
        msg = await ws_client.receive_json()
        expect(msg["event"]["type"]).to_equal("status")
        expect(msg["event"]["is_loading"]).to_be_falsy()

        await ws_client.client.session.close()

        # Allow lingering tasks to complete
        await asyncio.sleep(0.1)
