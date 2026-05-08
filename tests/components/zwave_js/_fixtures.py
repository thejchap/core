"""Tryke fixtures for the zwave_js integration.

Ports the relevant bits of the 1515-line ``conftest.py`` to tryke fixtures.

Design:

* Config-flow-only fixtures (``mock_setup_entry``, ``serial_port``,
  ``set_country``, ...) — the originals seeded by an earlier specialist.
* The deep mock chain (``client`` / ``integration`` / per-device nodes) —
  this slice. Each node has both a JSON-state loader fixture and a Node
  fixture, mirroring conftest.py 1:1 for portability.

The ``client`` fixture instantiates a real ``zwave_js_server.model.Driver``
from the controller-state JSON and attaches a real ``Node`` for the
controller. Per-device fixtures construct a ``Node`` from the device JSON
and register it on ``client.driver.controller.nodes``.

The ``integration`` fixture wires a ``MockConfigEntry`` and walks
``hass.config_entries.async_setup`` so platform forwarding fires.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
import copy
import dataclasses
import logging
from typing import Any
from unittest.mock import DEFAULT, AsyncMock, MagicMock, patch

from tryke import Depends, fixture
from zwave_js_server.model.driver import Driver
from zwave_js_server.model.node import Node
from zwave_js_server.version import VersionInfo

from homeassistant.components.usb import SerialDevice, USBDevice
from homeassistant.components.zwave_js import PLATFORMS
from homeassistant.components.zwave_js.const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture


# ---------------------------------------------------------------------------
# Config-flow-only fixtures (originals from earlier seed).
# ---------------------------------------------------------------------------


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Patch ``async_setup_entry`` to short-circuit integration setup."""
    with patch(
        "homeassistant.components.zwave_js.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@fixture
def mock_unload_entry() -> Generator[AsyncMock]:
    """Patch ``async_unload_entry`` to short-circuit integration teardown."""
    with patch(
        "homeassistant.components.zwave_js.async_unload_entry", return_value=True
    ) as unload_entry:
        yield unload_entry


@fixture
def mock_supervisor() -> Generator[None]:
    """Patch ``is_hassio`` to make the supervisor branch active."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.is_hassio", return_value=True
    ):
        yield


@fixture
def serial_port() -> USBDevice:
    """Return a representative mock serial port."""
    return USBDevice(
        device="/test",
        vid="162E",
        pid="269C",
        serial_number="1234",
        manufacturer="Virtual serial port",
        description="Some serial port",
    )


@fixture
def mock_scan_serial_ports(
    serial_port: USBDevice = Depends(serial_port),
) -> Generator[MagicMock]:
    """Patch ``async_scan_serial_ports`` with a representative fixture set."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports"
    ) as mock_scan:
        another_port = USBDevice(
            device="/new",
            vid="162E",
            pid="223D",
            serial_number="5678",
            manufacturer="Virtual serial port",
            description="New serial port",
        )

        no_vid_port = SerialDevice(
            device="/no_vid",
            description="Port without vid",
            serial_number="9123",
            manufacturer=None,
        )

        mock_scan.return_value = [serial_port, another_port, no_vid_port]
        yield mock_scan


@fixture
def mock_usb_serial_by_id() -> Generator[MagicMock]:
    """Patch ``usb.get_serial_by_id`` to return its input unchanged."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.get_serial_by_id"
    ) as mock_get_serial_by_id:
        mock_get_serial_by_id.side_effect = lambda x: x
        yield mock_get_serial_by_id


@fixture
def mock_addon_setup_time() -> Generator[None]:
    """Drop the add-on setup wait time to zero."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.ADDON_SETUP_TIMEOUT", new=0
    ):
        yield


@fixture
def mock_get_server_version() -> Generator[AsyncMock]:
    """Patch ``get_server_version`` with a usable VersionInfo."""
    version_info = VersionInfo(
        driver_version="mock-driver-version",
        server_version="mock-server-version",
        home_id=1234,
        min_schema_version=0,
        max_schema_version=1,
    )
    with patch(
        "homeassistant.components.zwave_js.helpers.get_server_version",
        return_value=version_info,
    ) as mock_version:
        yield mock_version


@fixture
def set_country(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Force the test ``HomeAssistant`` instance into a known country."""
    original_country = hass.config.country
    hass.config.country = "US"
    yield
    hass.config.country = original_country


def _set_home_id(get_server_version: AsyncMock, home_id: int) -> None:
    """Update the mocked server version's home_id (frozen dataclass)."""
    get_server_version.return_value = dataclasses.replace(
        get_server_version.return_value, home_id=home_id
    )


# ---------------------------------------------------------------------------
# State JSON loader helpers and fixtures.
# ---------------------------------------------------------------------------


def _load_state(filename: str) -> dict[str, Any]:
    """Load a Z-Wave JS state JSON fixture by filename."""
    return load_json_object_fixture(filename, DOMAIN)


@fixture
def controller_state() -> dict[str, Any]:
    """Load the controller state fixture data."""
    return _load_state("controller_state.json")


@fixture
def controller_node_state() -> dict[str, Any]:
    """Load the controller node state fixture data."""
    return _load_state("controller_node_state.json")


@fixture
def version_state() -> dict[str, Any]:
    """Return the version state fixture data."""
    return {
        "type": "version",
        "driverVersion": "6.0.0-beta.0",
        "serverVersion": "1.0.0",
        "homeId": 1234567890,
    }


@fixture
def log_config_state() -> dict[str, Any]:
    """Return log config state fixture data."""
    return {
        "enabled": True,
        "level": "info",
        "logToFile": False,
        "filename": "",
        "forceConsole": False,
    }


@fixture
def listen_block() -> asyncio.Event:
    """Mock a listen block event."""
    return asyncio.Event()


# ---------------------------------------------------------------------------
# Mock client / driver / controller deep chain.
# ---------------------------------------------------------------------------


@fixture
def get_server_version() -> Generator[AsyncMock]:
    """Mock server version (autouse-equivalent in conftest.py)."""
    version_info = VersionInfo(
        driver_version="mock-driver-version",
        server_version="mock-server-version",
        home_id=1234,
        min_schema_version=0,
        max_schema_version=1,
    )
    with (
        patch(
            "homeassistant.components.zwave_js.helpers.get_server_version",
            return_value=version_info,
        ) as mock_version,
        patch(
            "homeassistant.components.zwave_js.helpers.SERVER_VERSION_TIMEOUT",
            new=30,
        ),
    ):
        yield mock_version


@fixture
def client(
    controller_state: dict[str, Any] = Depends(controller_state),
    controller_node_state: dict[str, Any] = Depends(controller_node_state),
    version_state: dict[str, Any] = Depends(version_state),
    log_config_state: dict[str, Any] = Depends(log_config_state),
    listen_block: asyncio.Event = Depends(listen_block),
    _server_version: AsyncMock = Depends(get_server_version),
) -> Generator[MagicMock]:
    """Mock a Z-Wave JS client.

    Mirrors ``conftest.py``'s ``client`` fixture: instantiates a real
    ``Driver`` from the controller state and wires async helpers
    (``connect``/``listen``/``disconnect``) onto an autospec'd
    ``ZwaveClient`` mock.
    """
    with patch(
        "homeassistant.components.zwave_js.ZwaveClient", autospec=True
    ) as client_class:
        client_mock: MagicMock = client_class.return_value

        async def connect() -> None:
            listen_block.clear()
            await asyncio.sleep(0)
            client_mock.connected = True

        async def listen(driver_ready: asyncio.Event) -> None:
            driver_ready.set()
            await listen_block.wait()

        async def disconnect() -> None:
            listen_block.set()
            client_mock.connected = False

        client_mock.connect = AsyncMock(side_effect=connect)
        client_mock.listen = AsyncMock(side_effect=listen)
        client_mock.disconnect = AsyncMock(side_effect=disconnect)
        client_mock.disable_server_logging = MagicMock()
        client_mock.driver = Driver(
            client_mock,
            copy.deepcopy(controller_state),
            copy.deepcopy(log_config_state),
        )
        controller_node = Node(client_mock, copy.deepcopy(controller_node_state))
        client_mock.driver.controller.nodes[controller_node.node_id] = (
            controller_node
        )

        client_mock.version = VersionInfo.from_message(version_state)
        client_mock.ws_server_url = "ws://test:3000/zjs"

        async def async_send_command_side_effect(
            message: dict[str, Any], require_schema: int | None = None
        ) -> Any:
            """Return the command response."""
            if message["command"] == "node.has_device_config_changed":
                return {"changed": False}
            return DEFAULT

        client_mock.async_send_command.return_value = {
            "result": {"success": True, "status": 255}
        }
        client_mock.async_send_command.side_effect = async_send_command_side_effect

        yield client_mock


def make_zwave_node(client_mock: MagicMock, state: dict[str, Any]) -> Node:
    """Build a :class:`Node` from a JSON state dict and attach to the client."""
    node = Node(client_mock, copy.deepcopy(state))
    client_mock.driver.controller.nodes[node.node_id] = node
    return node


# ---------------------------------------------------------------------------
# Per-device state JSON fixtures (the ones we wire below + a few extras).
# Each is a 2-step pattern matching conftest.py: state fixture + node fixture.
# ---------------------------------------------------------------------------


def _state_fixture(filename: str):
    """Build a state-loading fixture for a JSON filename.

    Returns a callable suitable for ``@fixture`` that loads the JSON once.
    """

    def _load() -> dict[str, Any]:
        return _load_state(filename)

    _load.__name__ = filename
    _load.__qualname__ = filename
    _load.__doc__ = f"Load {filename} fixture data."
    return _load


# multisensor 6
@fixture
def multisensor_6_state() -> dict[str, Any]:
    """Load multisensor_6_state.json."""
    return _load_state("multisensor_6_state.json")


@fixture
def multisensor_6(
    client: MagicMock = Depends(client),
    multisensor_6_state: dict[str, Any] = Depends(multisensor_6_state),
) -> Node:
    """Mock a multisensor 6 node."""
    return make_zwave_node(client, multisensor_6_state)


# ecolink_door_sensor
@fixture
def ecolink_door_sensor_state() -> dict[str, Any]:
    """Load ecolink_door_sensor_state.json."""
    return _load_state("ecolink_door_sensor_state.json")


@fixture
def ecolink_door_sensor(
    client: MagicMock = Depends(client),
    ecolink_door_sensor_state: dict[str, Any] = Depends(ecolink_door_sensor_state),
) -> Node:
    """Mock an Ecolink door/window sensor node."""
    return make_zwave_node(client, ecolink_door_sensor_state)


# hank_binary_switch
@fixture
def hank_binary_switch_state() -> dict[str, Any]:
    """Load hank_binary_switch_state.json."""
    return _load_state("hank_binary_switch_state.json")


@fixture
def hank_binary_switch(
    client: MagicMock = Depends(client),
    hank_binary_switch_state: dict[str, Any] = Depends(hank_binary_switch_state),
) -> Node:
    """Mock a Hank binary switch node."""
    return make_zwave_node(client, hank_binary_switch_state)


# bulb_6_multi_color
@fixture
def bulb_6_multi_color_state() -> dict[str, Any]:
    """Load bulb_6_multi_color_state.json."""
    return _load_state("bulb_6_multi_color_state.json")


@fixture
def bulb_6_multi_color(
    client: MagicMock = Depends(client),
    bulb_6_multi_color_state: dict[str, Any] = Depends(bulb_6_multi_color_state),
) -> Node:
    """Mock a bulb 6 multi-color node."""
    return make_zwave_node(client, bulb_6_multi_color_state)


# lock_schlage_be469
@fixture
def lock_schlage_be469_state() -> dict[str, Any]:
    """Load lock_schlage_be469_state.json."""
    return _load_state("lock_schlage_be469_state.json")


@fixture
def lock_schlage_be469(
    client: MagicMock = Depends(client),
    lock_schlage_be469_state: dict[str, Any] = Depends(lock_schlage_be469_state),
) -> Node:
    """Mock a Schlage BE469 lock node."""
    return make_zwave_node(client, lock_schlage_be469_state)


# climate_radio_thermostat_ct100_plus
@fixture
def climate_radio_thermostat_ct100_plus_state() -> dict[str, Any]:
    """Load climate_radio_thermostat_ct100_plus_state.json."""
    return _load_state("climate_radio_thermostat_ct100_plus_state.json")


@fixture
def climate_radio_thermostat_ct100_plus(
    client: MagicMock = Depends(client),
    climate_radio_thermostat_ct100_plus_state: dict[str, Any] = Depends(
        climate_radio_thermostat_ct100_plus_state
    ),
) -> Node:
    """Mock a climate radio thermostat ct100 plus node."""
    return make_zwave_node(client, climate_radio_thermostat_ct100_plus_state)


# nortek_thermostat
@fixture
def nortek_thermostat_state() -> dict[str, Any]:
    """Load nortek_thermostat_state.json."""
    return _load_state("nortek_thermostat_state.json")


@fixture
def nortek_thermostat(
    client: MagicMock = Depends(client),
    nortek_thermostat_state: dict[str, Any] = Depends(nortek_thermostat_state),
) -> Node:
    """Mock a Nortek thermostat node."""
    return make_zwave_node(client, nortek_thermostat_state)


# fan_generic
@fixture
def fan_generic_state() -> dict[str, Any]:
    """Load fan_generic_state.json."""
    return _load_state("fan_generic_state.json")


@fixture
def fan_generic(
    client: MagicMock = Depends(client),
    fan_generic_state: dict[str, Any] = Depends(fan_generic_state),
) -> Node:
    """Mock a fan generic node."""
    return make_zwave_node(client, fan_generic_state)


# chain_actuator_zws12 (window cover)
@fixture
def chain_actuator_zws12_state() -> dict[str, Any]:
    """Load chain_actuator_zws12_state.json."""
    return _load_state("chain_actuator_zws12_state.json")


@fixture
def chain_actuator_zws12(
    client: MagicMock = Depends(client),
    chain_actuator_zws12_state: dict[str, Any] = Depends(chain_actuator_zws12_state),
) -> Node:
    """Mock a chain actuator ZWS12 cover node."""
    return make_zwave_node(client, chain_actuator_zws12_state)


# iblinds_v2
@fixture
def iblinds_v2_state() -> dict[str, Any]:
    """Load cover_iblinds_v2_state.json."""
    return _load_state("cover_iblinds_v2_state.json")


@fixture
def iblinds_v2(
    client: MagicMock = Depends(client),
    iblinds_v2_state: dict[str, Any] = Depends(iblinds_v2_state),
) -> Node:
    """Mock an iBlinds v2 node."""
    return make_zwave_node(client, iblinds_v2_state)


# zvidar
@fixture
def zvidar_state() -> dict[str, Any]:
    """Load cover_zvidar_state.json."""
    return _load_state("cover_zvidar_state.json")


@fixture
def zvidar(
    client: MagicMock = Depends(client),
    zvidar_state: dict[str, Any] = Depends(zvidar_state),
) -> Node:
    """Mock a ZVIDAR cover node."""
    return make_zwave_node(client, zvidar_state)


# touchwand_glass9
@fixture
def touchwand_glass9_state() -> dict[str, Any]:
    """Load touchwand_glass9_state.json."""
    return _load_state("touchwand_glass9_state.json")


@fixture
def touchwand_glass9(
    client: MagicMock = Depends(client),
    touchwand_glass9_state: dict[str, Any] = Depends(touchwand_glass9_state),
) -> Node:
    """Mock a Touchwand Glass 9 node."""
    return make_zwave_node(client, touchwand_glass9_state)


# aeon_smart_switch_6
@fixture
def aeon_smart_switch_6_state() -> dict[str, Any]:
    """Load aeon_smart_switch_6_state.json."""
    return _load_state("aeon_smart_switch_6_state.json")


@fixture
def aeon_smart_switch_6(
    client: MagicMock = Depends(client),
    aeon_smart_switch_6_state: dict[str, Any] = Depends(aeon_smart_switch_6_state),
) -> Node:
    """Mock an Aeon Smart Switch 6 node."""
    return make_zwave_node(client, aeon_smart_switch_6_state)


# ge_12730 (fan)
@fixture
def ge_12730_state() -> dict[str, Any]:
    """Load fan_ge_12730_state.json."""
    return _load_state("fan_ge_12730_state.json")


@fixture
def ge_12730(
    client: MagicMock = Depends(client),
    ge_12730_state: dict[str, Any] = Depends(ge_12730_state),
) -> Node:
    """Mock a GE 12730 fan controller node."""
    return make_zwave_node(client, ge_12730_state)


# enbrighten_58446_zwa4013
@fixture
def enbrighten_58446_zwa4013_state() -> dict[str, Any]:
    """Load enbrighten_58446_zwa4013_state.json."""
    return _load_state("enbrighten_58446_zwa4013_state.json")


@fixture
def enbrighten_58446_zwa4013(
    client: MagicMock = Depends(client),
    enbrighten_58446_zwa4013_state: dict[str, Any] = Depends(
        enbrighten_58446_zwa4013_state
    ),
) -> Node:
    """Mock an Enbrighten 58446 ZWA4013 node."""
    return make_zwave_node(client, enbrighten_58446_zwa4013_state)


# inovelli_lzw36
@fixture
def inovelli_lzw36_state() -> dict[str, Any]:
    """Load inovelli_lzw36_state.json."""
    return _load_state("inovelli_lzw36_state.json")


@fixture
def inovelli_lzw36(
    client: MagicMock = Depends(client),
    inovelli_lzw36_state: dict[str, Any] = Depends(inovelli_lzw36_state),
) -> Node:
    """Mock an Inovelli LZW36 fan controller node."""
    return make_zwave_node(client, inovelli_lzw36_state)


# vision_security_zl7432
@fixture
def vision_security_zl7432_state() -> dict[str, Any]:
    """Load vision_security_zl7432_state.json."""
    return _load_state("vision_security_zl7432_state.json")


@fixture
def vision_security_zl7432(
    client: MagicMock = Depends(client),
    vision_security_zl7432_state: dict[str, Any] = Depends(
        vision_security_zl7432_state
    ),
) -> Node:
    """Mock a Vision Security ZL7432 node."""
    return make_zwave_node(client, vision_security_zl7432_state)


# lock_popp_electric_strike_lock_control
@fixture
def lock_popp_electric_strike_lock_control_state() -> dict[str, Any]:
    """Load lock_popp_electric_strike_lock_control_state.json."""
    return _load_state("lock_popp_electric_strike_lock_control_state.json")


@fixture
def lock_popp_electric_strike_lock_control(
    client: MagicMock = Depends(client),
    lock_popp_electric_strike_lock_control_state: dict[str, Any] = Depends(
        lock_popp_electric_strike_lock_control_state
    ),
) -> Node:
    """Mock a Popp electric strike lock control node."""
    return make_zwave_node(client, lock_popp_electric_strike_lock_control_state)


# fortrezz_ssa2_siren
@fixture
def fortrezz_ssa2_siren_state() -> dict[str, Any]:
    """Load fortrezz_ssa2_siren_state.json."""
    return _load_state("fortrezz_ssa2_siren_state.json")


@fixture
def fortrezz_ssa2_siren(
    client: MagicMock = Depends(client),
    fortrezz_ssa2_siren_state: dict[str, Any] = Depends(fortrezz_ssa2_siren_state),
) -> Node:
    """Mock a FortrezZ SSA2 siren node."""
    return make_zwave_node(client, fortrezz_ssa2_siren_state)


# fortrezz_ssa3_siren
@fixture
def fortrezz_ssa3_siren_state() -> dict[str, Any]:
    """Load fortrezz_ssa3_siren_state.json."""
    return _load_state("fortrezz_ssa3_siren_state.json")


@fixture
def fortrezz_ssa3_siren(
    client: MagicMock = Depends(client),
    fortrezz_ssa3_siren_state: dict[str, Any] = Depends(fortrezz_ssa3_siren_state),
) -> Node:
    """Mock a FortrezZ SSA3 siren node."""
    return make_zwave_node(client, fortrezz_ssa3_siren_state)


# merten_507801
@fixture
def merten_507801_state() -> dict[str, Any]:
    """Load cover_merten_507801_state.json."""
    return _load_state("cover_merten_507801_state.json")


@fixture
def merten_507801(
    client: MagicMock = Depends(client),
    merten_507801_state: dict[str, Any] = Depends(merten_507801_state),
) -> Node:
    """Mock a Merten 507801 cover node."""
    return make_zwave_node(client, merten_507801_state)


# shelly QNSH 001P10
@fixture
def shelly_europe_ltd_qnsh_001p10_state() -> dict[str, Any]:
    """Load shelly_europe_ltd_qnsh_001p10_state.json."""
    return _load_state("shelly_europe_ltd_qnsh_001p10_state.json")


@fixture
def shelly_qnsh_001P10_shutter(
    client: MagicMock = Depends(client),
    shelly_europe_ltd_qnsh_001p10_state: dict[str, Any] = Depends(
        shelly_europe_ltd_qnsh_001p10_state
    ),
) -> Node:
    """Mock a Shelly QNSH 001P10 shutter node."""
    return make_zwave_node(client, shelly_europe_ltd_qnsh_001p10_state)


# switch_zooz_zen72
@fixture
def switch_zooz_zen72_state() -> dict[str, Any]:
    """Load switch_zooz_zen72_state.json."""
    return _load_state("switch_zooz_zen72_state.json")


@fixture
def switch_zooz_zen72(
    client: MagicMock = Depends(client),
    switch_zooz_zen72_state: dict[str, Any] = Depends(switch_zooz_zen72_state),
) -> Node:
    """Mock a Zooz Zen72 switch node."""
    return make_zwave_node(client, switch_zooz_zen72_state)


# indicator_test
@fixture
def indicator_test_state() -> dict[str, Any]:
    """Load indicator_test_state.json."""
    return _load_state("indicator_test_state.json")


@fixture
def indicator_test(
    client: MagicMock = Depends(client),
    indicator_test_state: dict[str, Any] = Depends(indicator_test_state),
) -> Node:
    """Mock an indicator-CC test node."""
    return make_zwave_node(client, indicator_test_state)


# light_device_class_is_null
@fixture
def light_device_class_is_null_state() -> dict[str, Any]:
    """Load light_device_class_is_null_state.json."""
    return _load_state("light_device_class_is_null_state.json")


@fixture
def light_device_class_is_null(
    client: MagicMock = Depends(client),
    light_device_class_is_null_state: dict[str, Any] = Depends(
        light_device_class_is_null_state
    ),
) -> Node:
    """Mock a node where the device class is null."""
    return make_zwave_node(client, light_device_class_is_null_state)


# aeotec_smart_switch_7
@fixture
def aeotec_smart_switch_7_state() -> dict[str, Any]:
    """Load aeotec_smart_switch_7_state.json."""
    return _load_state("aeotec_smart_switch_7_state.json")


@fixture
def aeotec_smart_switch_7(
    client: MagicMock = Depends(client),
    aeotec_smart_switch_7_state: dict[str, Any] = Depends(aeotec_smart_switch_7_state),
) -> Node:
    """Mock an Aeotec Smart Switch 7 node."""
    return make_zwave_node(client, aeotec_smart_switch_7_state)


# nabu_casa_zwa2
@fixture
def nabu_casa_zwa2_state() -> dict[str, Any]:
    """Load nabu_casa_zwa2_state.json."""
    return _load_state("nabu_casa_zwa2_state.json")


@fixture
def nabu_casa_zwa2(
    client: MagicMock = Depends(client),
    nabu_casa_zwa2_state: dict[str, Any] = Depends(nabu_casa_zwa2_state),
) -> Node:
    """Mock a Nabu Casa ZWA-2 node."""
    return make_zwave_node(client, nabu_casa_zwa2_state)


@fixture
def nabu_casa_zwa2_legacy_state() -> dict[str, Any]:
    """Load nabu_casa_zwa2_legacy_state.json."""
    return _load_state("nabu_casa_zwa2_legacy_state.json")


@fixture
def nabu_casa_zwa2_legacy(
    client: MagicMock = Depends(client),
    nabu_casa_zwa2_legacy_state: dict[str, Any] = Depends(nabu_casa_zwa2_legacy_state),
) -> Node:
    """Mock a Nabu Casa ZWA-2 (legacy fw) node."""
    return make_zwave_node(client, nabu_casa_zwa2_legacy_state)


# fibaro_fgms001_v2_8
@fixture
def fibaro_fgms001_v2_8_state() -> dict[str, Any]:
    """Load fibaro_fgms001_v2_8_state.json."""
    return _load_state("fibaro_fgms001_v2_8_state.json")


@fixture
def fibaro_fgms001_v2_8(
    client: MagicMock = Depends(client),
    fibaro_fgms001_v2_8_state: dict[str, Any] = Depends(fibaro_fgms001_v2_8_state),
) -> Node:
    """Mock a Fibaro FGMS001 (v2.8) motion sensor node."""
    return make_zwave_node(client, fibaro_fgms001_v2_8_state)


# wallmote_central_scene
@fixture
def wallmote_central_scene_state() -> dict[str, Any]:
    """Load wallmote_central_scene_state.json."""
    return _load_state("wallmote_central_scene_state.json")


@fixture
def wallmote_central_scene(
    client: MagicMock = Depends(client),
    wallmote_central_scene_state: dict[str, Any] = Depends(wallmote_central_scene_state),
) -> Node:
    """Mock a Wallmote central-scene node."""
    return make_zwave_node(client, wallmote_central_scene_state)


# climate_radio_thermostat_ct100_plus_different_endpoints
@fixture
def climate_radio_thermostat_ct100_plus_different_endpoints_state() -> dict[str, Any]:
    """Load climate_radio_thermostat_ct100_plus_different_endpoints_state.json."""
    return _load_state(
        "climate_radio_thermostat_ct100_plus_different_endpoints_state.json"
    )


@fixture
def climate_radio_thermostat_ct100_plus_different_endpoints(
    client: MagicMock = Depends(client),
    state: dict[str, Any] = Depends(
        climate_radio_thermostat_ct100_plus_different_endpoints_state
    ),
) -> Node:
    """Mock a CT100 plus thermostat with values on different endpoints."""
    return make_zwave_node(client, state)


# null_name_check
@fixture
def null_name_check_state() -> dict[str, Any]:
    """Load null_name_check_state.json."""
    return _load_state("null_name_check_state.json")


@fixture
def null_name_check(
    client: MagicMock = Depends(client),
    null_name_check_state: dict[str, Any] = Depends(null_name_check_state),
) -> Node:
    """Mock a node with a null name."""
    return make_zwave_node(client, null_name_check_state)


# ---------------------------------------------------------------------------
# Integration setup fixture.
# ---------------------------------------------------------------------------


@fixture
def platforms() -> list[Platform]:
    """Override-able platform list for integration setup."""
    return PLATFORMS


@fixture
async def integration(
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    platforms: list[Platform] = Depends(platforms),
) -> MockConfigEntry:
    """Set up the zwave_js integration with the mocked client.

    Mirrors the conftest.py ``integration`` fixture: builds a
    ``MockConfigEntry``, walks ``async_setup``, then resets the
    ``async_send_command`` mock so per-test assertions are clean.
    """
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org"},
        unique_id=str(client.driver.controller.home_id),
    )
    entry.add_to_hass(hass)
    with patch("homeassistant.components.zwave_js.PLATFORMS", platforms):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    client.async_send_command.reset_mock()
    return entry


@fixture
async def integration_no_platforms(
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
) -> MockConfigEntry:
    """Same as ``integration`` but with no platforms (faster)."""
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org"},
        unique_id=str(client.driver.controller.home_id),
    )
    entry.add_to_hass(hass)
    with patch("homeassistant.components.zwave_js.PLATFORMS", []):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    client.async_send_command.reset_mock()
    return entry


@fixture
def connect_timeout() -> Generator[MagicMock]:
    """Mock the connect timeout at zero."""
    with patch(
        "homeassistant.components.zwave_js.CONNECT_TIMEOUT", new=0
    ) as timeout:
        yield timeout


__all__ = [
    "_set_home_id",
    "aeon_smart_switch_6",
    "aeon_smart_switch_6_state",
    "aeotec_smart_switch_7",
    "aeotec_smart_switch_7_state",
    "bulb_6_multi_color",
    "bulb_6_multi_color_state",
    "chain_actuator_zws12",
    "chain_actuator_zws12_state",
    "client",
    "climate_radio_thermostat_ct100_plus",
    "climate_radio_thermostat_ct100_plus_state",
    "connect_timeout",
    "controller_node_state",
    "controller_state",
    "ecolink_door_sensor",
    "ecolink_door_sensor_state",
    "enbrighten_58446_zwa4013",
    "enbrighten_58446_zwa4013_state",
    "fan_generic",
    "fan_generic_state",
    "fibaro_fgms001_v2_8",
    "fibaro_fgms001_v2_8_state",
    "fortrezz_ssa2_siren",
    "fortrezz_ssa2_siren_state",
    "fortrezz_ssa3_siren",
    "fortrezz_ssa3_siren_state",
    "ge_12730",
    "ge_12730_state",
    "get_server_version",
    "hank_binary_switch",
    "hank_binary_switch_state",
    "iblinds_v2",
    "iblinds_v2_state",
    "indicator_test",
    "indicator_test_state",
    "inovelli_lzw36",
    "inovelli_lzw36_state",
    "integration",
    "integration_no_platforms",
    "light_device_class_is_null",
    "light_device_class_is_null_state",
    "listen_block",
    "lock_popp_electric_strike_lock_control",
    "lock_popp_electric_strike_lock_control_state",
    "lock_schlage_be469",
    "lock_schlage_be469_state",
    "log_config_state",
    "make_zwave_node",
    "merten_507801",
    "merten_507801_state",
    "mock_addon_setup_time",
    "mock_get_server_version",
    "mock_scan_serial_ports",
    "mock_setup_entry",
    "mock_supervisor",
    "mock_unload_entry",
    "mock_usb_serial_by_id",
    "multisensor_6",
    "multisensor_6_state",
    "nabu_casa_zwa2",
    "nabu_casa_zwa2_legacy",
    "nabu_casa_zwa2_legacy_state",
    "nabu_casa_zwa2_state",
    "nortek_thermostat",
    "nortek_thermostat_state",
    "null_name_check",
    "null_name_check_state",
    "platforms",
    "serial_port",
    "set_country",
    "shelly_europe_ltd_qnsh_001p10_state",
    "shelly_qnsh_001P10_shutter",
    "switch_zooz_zen72",
    "switch_zooz_zen72_state",
    "touchwand_glass9",
    "touchwand_glass9_state",
    "version_state",
    "vision_security_zl7432",
    "vision_security_zl7432_state",
    "wallmote_central_scene",
    "wallmote_central_scene_state",
    "climate_radio_thermostat_ct100_plus_different_endpoints",
    "climate_radio_thermostat_ct100_plus_different_endpoints_state",
    "zvidar",
    "zvidar_state",
]
