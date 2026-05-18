"""Tests for Shelly diagnostics platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import ANY, Mock, PropertyMock

from aioshelly.ble.const import BLE_SCAN_RESULT_EVENT
from aioshelly.const import MODEL_25
from aioshelly.exceptions import DeviceConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.diagnostics import REDACTED
from homeassistant.components.shelly.const import (
    CONF_BLE_SCANNER_MODE,
    DOMAIN,
    BLEScannerMode,
)
from homeassistant.components.shelly.diagnostics import TO_REDACT
from homeassistant.core import HomeAssistant

from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.components.shelly import init_integration, inject_rpc_device_event
from tests.components.shelly._fixtures import (
    MOCK_STATUS_COAP,
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)

_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

    try:
        yield _Patcher()
    finally:
        for kind, obj, key, original in reversed(undo):
            if kind == "attr":
                if original is _MISSING:
                    with suppress(AttributeError):
                        delattr(obj, key)
                else:
                    setattr(obj, key, original)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def block_config_entry_diagnostics(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test config entry diagnostics for block device."""
    await init_integration(hass, 1)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entry_dict = entry.as_dict()
    entry_dict["data"].update(
        {key: REDACTED for key in TO_REDACT if key in entry_dict["data"]}
    )

    type(mock_block_device).last_error = PropertyMock(
        return_value=DeviceConnectionError()
    )

    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    expect(result).to_equal(
        {
            "entry": entry_dict | {"discovery_keys": {}},
            "bluetooth": "not initialized",
            "device_info": {
                "name": "Test name",
                "model": MODEL_25,
                "sw_version": "some fw string",
            },
            "device_settings": {
                "coiot": {
                    "update_period": 15,
                    "enabled": True,
                    "peer": "10.10.10.10:5683",
                }
            },
            "device_status": MOCK_STATUS_COAP,
            "last_error": "DeviceConnectionError()",
        }
    )


@test
async def rpc_config_entry_diagnostics(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test config entry diagnostics for rpc device."""
    with _patches() as monkeypatch:
        await init_integration(
            hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
        )

        inject_rpc_device_event(
            monkeypatch,
            mock_rpc_device,
            {
                "events": [
                    {
                        "component": "script:1",
                        "data": [
                            1,
                            "aa:bb:cc:dd:ee:ff",
                            -62,
                            "AgEGCf9ZANH7O3TIkA==",
                            "EQcbxdWlAgC4n+YRTSIADaLLBhYADUgQYQ==",
                        ],
                        "event": BLE_SCAN_RESULT_EVENT,
                        "id": 1,
                        "ts": 1668522399.2,
                    }
                ],
                "ts": 1668522399.2,
            },
        )

        entry = hass.config_entries.async_entries(DOMAIN)[0]
        entry_dict = entry.as_dict()
        entry_dict["data"].update(
            {key: REDACTED for key in TO_REDACT if key in entry_dict["data"]}
        )

        type(mock_rpc_device).last_error = PropertyMock(
            return_value=DeviceConnectionError()
        )

        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)
        expect(result).to_equal(
            {
                "entry": entry_dict | {"discovery_keys": {}},
                "bluetooth": {
                    "scanner": {
                        "connectable": False,
                        "current_mode": {
                            "__type": "<enum 'BluetoothScanningMode'>",
                            "repr": "<BluetoothScanningMode.ACTIVE: 'active'>",
                        },
                        "requested_mode": {
                            "__type": "<enum 'BluetoothScanningMode'>",
                            "repr": "<BluetoothScanningMode.ACTIVE: 'active'>",
                        },
                        "discovered_device_timestamps": {"AA:BB:CC:DD:EE:FF": ANY},
                        "discovered_devices_and_advertisement_data": [
                            {
                                "address": "AA:BB:CC:DD:EE:FF",
                                "advertisement_data": [
                                    None,
                                    {
                                        "89": {
                                            "__type": "<class 'bytes'>",
                                            "repr": "b'\\xd1\\xfb;t\\xc8\\x90'",
                                        }
                                    },
                                    {
                                        "00000d00-0000-1000-8000-00805f9b34fb": {
                                            "__type": "<class 'bytes'>",
                                            "repr": "b'H\\x10a'",
                                        }
                                    },
                                    ["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
                                    -127,
                                    -62,
                                    [],
                                ],
                                "details": {"source": "12:34:56:78:9A:BE"},
                                "name": None,
                                "rssi": -62,
                            }
                        ],
                        "last_detection": ANY,
                        "monotonic_time": ANY,
                        "name": "Test name (12:34:56:78:9A:BE)",
                        "scanning": True,
                        "start_time": ANY,
                        "source": "12:34:56:78:9A:BE",
                        "time_since_last_device_detection": {"AA:BB:CC:DD:EE:FF": ANY},
                        "raw_advertisement_data": {
                            "AA:BB:CC:DD:EE:FF": {
                                "__type": "<class 'bytes'>",
                                "repr": "b'\\x02\\x01\\x06\\t\\xffY\\x00\\xd1\\xfb;t\\xc8\\x90\\x11\\x07\\x1b\\xc5\\xd5\\xa5\\x02\\x00\\xb8\\x9f\\xe6\\x11M\"\\x00\\r\\xa2\\xcb\\x06\\x16\\x00\\rH\\x10a'",
                            }
                        },
                        "type": "ShellyBLEScanner",
                    }
                },
                "device_info": {
                    "name": "Test name",
                    "model": MODEL_25,
                    "sw_version": "some fw string",
                },
                "device_settings": {"ws_outbound_enabled": False},
                "device_status": {
                    "sys": {
                        "available_updates": {
                            "beta": {"version": "some_beta_version"},
                            "stable": {"version": "some_beta_version"},
                        },
                        "relay_in_thermostat": True,
                    },
                    "wifi": {"rssi": -63},
                },
                "last_error": "DeviceConnectionError()",
            }
        )


@test.cases(
    test.case(
        "valid",
        ws_outbound_server="ws://10.10.10.10:8123/api/shelly/ws",
        ws_outbound_server_valid=True,
    ),
    test.case(
        "invalid",
        ws_outbound_server="wrong_url",
        ws_outbound_server_valid=False,
    ),
)
async def rpc_config_entry_diagnostics_ws_outbound(
    ws_outbound_server: str,
    ws_outbound_server_valid: bool,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test config entry diagnostics for rpc device with websocket outbound."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config["ws"] = {"enable": True, "server": ws_outbound_server}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        entry = await init_integration(hass, 2, sleep_period=60)

        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

        expect(result["device_settings"]["ws_outbound_server_valid"]).to_equal(
            ws_outbound_server_valid
        )


@test
async def rpc_config_entry_diagnostics_no_ws(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test config entry diagnostics for rpc device which doesn't support ws outbound."""
    with _patches() as monkeypatch:
        config = deepcopy(mock_rpc_device.config)
        config.pop("ws")
        monkeypatch.setattr(mock_rpc_device, "config", config)

        entry = await init_integration(hass, 3)

        result = await get_diagnostics_for_config_entry(hass, hass_client, entry)

        expect(result["device_settings"]["ws_outbound"]).to_equal("not supported")
