"""Test repairs handling for Shelly (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Any
from unittest.mock import Mock, patch

from aioshelly.const import MODEL_PLUG, MODEL_WALL_DISPLAY
from aioshelly.exceptions import DeviceConnectionError, RpcCallError
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly.const import (
    BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID,
    COIOT_UNCONFIGURED_ISSUE_ID,
    CONF_BLE_SCANNER_MODE,
    DEPRECATED_FIRMWARE_ISSUE_ID,
    DOMAIN,
    OPEN_WIFI_AP_ISSUE_ID,
    OUTBOUND_WEBSOCKET_INCORRECTLY_ENABLED_ISSUE_ID,
    PUSH_UPDATE_ISSUE_ID,
    BLEScannerMode,
    DeprecatedFirmwareInfo,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.network import NoURLAvailableError
from homeassistant.setup import async_setup_component

from tests.components.repairs import (
    async_process_repairs_platforms,
    process_repair_fix_flow,
    start_repair_fix_flow,
)
from tests.components.shelly import (
    MOCK_MAC,
    init_integration,
    mock_block_device_push_update_failure,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    issue_registry as issue_registry_fixture,
    mock_network,
)

_MISSING = object()


@contextmanager
def _patches() -> Generator[Any]:
    """Mimic pytest's monkeypatch for setattr/setitem/delattr/delitem."""

    undo: list[Any] = []

    class _Patcher:
        def setattr(self, target: Any, name: str, value: Any) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            setattr(target, name, value)

        def setitem(self, mapping: Any, key: Any, value: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping[key] = value

        def delitem(self, mapping: Any, key: Any) -> None:
            original = mapping.get(key, _MISSING)
            undo.append(("item", mapping, key, original))
            mapping.pop(key, None)

        def delattr(self, target: Any, name: str) -> None:
            original = getattr(target, name, _MISSING)
            undo.append(("attr", target, name, original))
            try:
                del target.__dict__[name]
            except (AttributeError, KeyError):
                with suppress(AttributeError):
                    delattr(target, name)

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
            elif original is _MISSING:
                obj.pop(key, None)
            else:
                obj[key] = original


def _resolve_exception(name: str) -> Exception | type[Exception]:
    """Resolve string identifier to exception (literal positionals only in cases)."""
    if name == "device_connection":
        return DeviceConnectionError
    if name == "rpc_call":
        return RpcCallError(999, "Unknown error")
    raise ValueError(f"Unknown exception identifier: {name}")


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def ble_scanner_unsupported_firmware_issue(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling for BLE scanner with unsupported firmware."""
    issue_id = BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=MOCK_MAC)
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await hass.async_block_till_done()
    await init_integration(
        hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
    )

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    expect(result["step_id"]).to_equal("confirm")

    result = await process_repair_fix_flow(client, flow_id)
    expect(result["type"]).to_equal("create_entry")
    expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(1)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
    expect(len(issue_registry.issues)).to_equal(0)


@test
async def unsupported_firmware_issue_update_not_available(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling when firmware update is not available."""
    with _patches() as monkeypatch:
        issue_id = BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(
            hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
        )

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("confirm")

        monkeypatch.setitem(mock_rpc_device.status, "sys", {"available_updates": {}})
        result = await process_repair_fix_flow(client, flow_id)
        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("update_not_available")
        expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(0)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)


@test.cases(
    test.case("device_connection", exception_name="device_connection"),
    test.case("rpc_call", exception_name="rpc_call"),
)
async def unsupported_firmware_issue_exc(
    exception_name: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling when OTA update ends with an exception."""
    exception = _resolve_exception(exception_name)
    issue_id = BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=MOCK_MAC)
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await hass.async_block_till_done()
    await init_integration(
        hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
    )

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    expect(result["step_id"]).to_equal("confirm")

    mock_rpc_device.trigger_ota_update.side_effect = exception
    result = await process_repair_fix_flow(client, flow_id)
    expect(result["type"]).to_equal("abort")
    expect(result["reason"]).to_equal("cannot_connect")
    expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(1)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)


@test
async def outbound_websocket_incorrectly_enabled_issue(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling for the outbound WebSocket incorrectly enabled."""
    with _patches() as monkeypatch:
        ws_url = "ws://10.10.10.10:8123/api/shelly/ws"
        monkeypatch.setitem(
            mock_rpc_device.config, "ws", {"enable": True, "server": ws_url}
        )

        issue_id = OUTBOUND_WEBSOCKET_INCORRECTLY_ENABLED_ISSUE_ID.format(
            unique=MOCK_MAC
        )
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("confirm")

        result = await process_repair_fix_flow(client, flow_id)
        expect(result["type"]).to_equal("create_entry")
        expect(mock_rpc_device.ws_setconfig.call_count).to_equal(1)
        expect(mock_rpc_device.ws_setconfig.call_args[0]).to_equal((False, ws_url))
        expect(mock_rpc_device.trigger_reboot.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test.cases(
    test.case("device_connection", exception_name="device_connection"),
    test.case("rpc_call", exception_name="rpc_call"),
)
async def outbound_websocket_incorrectly_enabled_issue_exc(
    exception_name: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling when ws_setconfig ends with an exception."""
    with _patches() as monkeypatch:
        exception = _resolve_exception(exception_name)
        ws_url = "ws://10.10.10.10:8123/api/shelly/ws"
        monkeypatch.setitem(
            mock_rpc_device.config, "ws", {"enable": True, "server": ws_url}
        )

        issue_id = OUTBOUND_WEBSOCKET_INCORRECTLY_ENABLED_ISSUE_ID.format(
            unique=MOCK_MAC
        )
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("confirm")

        mock_rpc_device.ws_setconfig.side_effect = exception
        result = await process_repair_fix_flow(client, flow_id)
        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("cannot_connect")
        expect(mock_rpc_device.ws_setconfig.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)


@test
async def deprecated_firmware_issue(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling deprecated firmware."""
    issue_id = DEPRECATED_FIRMWARE_ISSUE_ID.format(unique=MOCK_MAC)
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.shelly.repairs.DEPRECATED_FIRMWARES",
        {
            MODEL_WALL_DISPLAY: DeprecatedFirmwareInfo(
                {"min_firmware": "2.3.0", "ha_version": "2025.10.0"}
            )
        },
    ):
        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    expect(result["step_id"]).to_equal("confirm")

    result = await process_repair_fix_flow(client, flow_id)
    expect(result["type"]).to_equal("create_entry")
    expect(mock_rpc_device.trigger_ota_update.call_count).to_equal(1)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
    expect(len(issue_registry.issues)).to_equal(0)


@test
async def open_wifi_ap_issue(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling for open WiFi AP."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": True, "is_open": True}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "confirm"}
        )
        expect(result["type"]).to_equal("create_entry")
        expect(mock_rpc_device.wifi_setconfig.call_count).to_equal(1)
        expect(mock_rpc_device.wifi_setconfig.call_args[1]).to_equal(
            {"ap_enable": False}
        )
        expect(mock_rpc_device.trigger_reboot.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test
async def open_wifi_ap_issue_no_restart(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling for open WiFi AP when restart not required."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": True, "is_open": True}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        mock_rpc_device.wifi_setconfig.return_value = {"restart_required": False}

        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "confirm"}
        )
        expect(result["type"]).to_equal("create_entry")
        expect(mock_rpc_device.wifi_setconfig.call_count).to_equal(1)
        expect(mock_rpc_device.wifi_setconfig.call_args[1]).to_equal(
            {"ap_enable": False}
        )
        expect(mock_rpc_device.trigger_reboot.call_count).to_equal(0)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test.cases(
    test.case("device_connection", exception_name="device_connection"),
    test.case("rpc_call", exception_name="rpc_call"),
)
async def open_wifi_ap_issue_exc(
    exception_name: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling when wifi_setconfig ends with an exception."""
    with _patches() as monkeypatch:
        exception = _resolve_exception(exception_name)
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": True, "is_open": True}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        mock_rpc_device.wifi_setconfig.side_effect = exception
        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "confirm"}
        )
        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("cannot_connect")
        expect(mock_rpc_device.wifi_setconfig.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)


@test
async def no_open_wifi_ap_issue_with_password(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test no repair issue is created when WiFi AP has a password."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": True, "is_open": False}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test
async def no_open_wifi_ap_issue_when_disabled(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test no repair issue is created when WiFi AP is disabled."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": False, "is_open": True}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test
async def open_wifi_ap_issue_ignore(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test ignoring the open WiFi AP issue."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_rpc_device.config,
            "wifi",
            {"ap": {"enable": True, "is_open": True}},
        )

        issue_id = OPEN_WIFI_AP_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 2)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "ignore"}
        )
        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("issue_ignored")
        expect(mock_rpc_device.wifi_setconfig.call_count).to_equal(0)

        issue = issue_registry.async_get_issue(DOMAIN, issue_id)
        expect(issue).to_be_truthy()
        expect(issue.dismissed_version).to_be_truthy()


@test
async def other_fixable_issues(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test fixing another issue."""
    issue_id = "other_issue"
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await hass.async_block_till_done()
    entry = await init_integration(hass, 2)
    expect(mock_rpc_device.initialized).to_be(True)

    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={"entry_id": entry.entry_id},
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="other_issue",
    )

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    expect(result["step_id"]).to_equal("confirm")
    expect(result["type"]).to_equal("form")

    result = await process_repair_fix_flow(client, flow_id)
    expect(result["type"]).to_equal("create_entry")


@test.cases(
    test.case(
        "disabled",
        coiot={"enabled": False, "update_period": 15, "peer": "10.10.10.10:5683"},
    ),
    test.case(
        "wrong_peer",
        coiot={"enabled": True, "update_period": 15, "peer": "7.7.7.7:5683"},
    ),
)
async def coiot_disabled_or_wrong_peer_issue(
    coiot: dict[str, Any],
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test repair issues handling wrong or disabled CoIoT configuration."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.settings, "coiot", coiot)
        issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1)
        await mock_block_device_push_update_failure(hass, mock_block_device)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "confirm"}
        )

        expect(result["type"]).to_equal("create_entry")
        expect(mock_block_device.configure_coiot_protocol.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_falsy()
        expect(len(issue_registry.issues)).to_equal(0)


@test
async def coiot_exception(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test CoIoT exception handling in fix flow."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "coiot",
            {"enabled": False, "update_period": 15, "peer": "7.7.7.7:5683"},
        )
        issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1)
        await mock_block_device_push_update_failure(hass, mock_block_device)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        mock_block_device.configure_coiot_protocol.side_effect = DeviceConnectionError
        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "confirm"}
        )

        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("cannot_connect")
        expect(mock_block_device.configure_coiot_protocol.call_count).to_equal(1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)


@test.cases(
    test.case("http", raw_url="http://10.10.10.10:8123"),
    test.case("https", raw_url="https://homeassistant.local:443"),
)
async def coiot_configured_no_issue_created(
    raw_url: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test no repair issues when CoIoT configuration is valid."""
    issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    with patch(
        "homeassistant.components.shelly.utils.get_url",
        return_value=raw_url,
    ):
        await hass.async_block_till_done()
        await init_integration(hass, 1)
        await mock_block_device_push_update_failure(hass, mock_block_device)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be(None)


@test
async def coiot_key_missing_no_issue_created(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test no repair issues when CoIoT configuration is missing."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(
            mock_block_device.settings,
            "coiot",
        )
        issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be(None)


@test
async def coiot_push_issue_when_missing_hass_url(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test CoIoT push update issue created when HA URL is not available."""
    issue_id = PUSH_UPDATE_ISSUE_ID.format(unique=MOCK_MAC)
    expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
    await hass.async_block_till_done()
    await init_integration(hass, 1)

    with patch(
        "homeassistant.components.shelly.utils.get_url",
        side_effect=NoURLAvailableError(),
    ):
        await mock_block_device_push_update_failure(hass, mock_block_device)

    expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
    expect(len(issue_registry.issues)).to_equal(1)


@test
async def coiot_fix_flow_no_hass_url(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test CoIoT repair issue when HA URL is not available."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "coiot",
            {"enabled": False, "update_period": 15, "peer": "7.7.7.7:5683"},
        )
        issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1)
        await mock_block_device_push_update_failure(hass, mock_block_device)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        with patch(
            "homeassistant.components.shelly.utils.get_url",
            side_effect=NoURLAvailableError(),
        ):
            result = await process_repair_fix_flow(
                client, flow_id, {"next_step_id": "confirm"}
            )

            expect(result["type"]).to_equal("abort")
            expect(result["reason"]).to_equal("cannot_configure")
            expect(mock_block_device.configure_coiot_protocol.call_count).to_equal(0)

            expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
            expect(len(issue_registry.issues)).to_equal(1)


@test
async def coiot_issue_ignore(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test ignoring the CoIoT unconfigured issue."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(
            mock_block_device.settings,
            "coiot",
            {"enabled": False, "update_period": 15, "peer": "7.7.7.7:5683"},
        )
        issue_id = COIOT_UNCONFIGURED_ISSUE_ID.format(unique=MOCK_MAC)

        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1)
        await mock_block_device_push_update_failure(hass, mock_block_device)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        await async_process_repairs_platforms(hass)
        client = await hass_client()
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)

        flow_id = result["flow_id"]
        expect(result["step_id"]).to_equal("init")
        expect(result["type"]).to_equal("menu")

        result = await process_repair_fix_flow(
            client, flow_id, {"next_step_id": "ignore"}
        )
        expect(result["type"]).to_equal("abort")
        expect(result["reason"]).to_equal("issue_ignored")
        expect(mock_block_device.configure_coiot_protocol.call_count).to_equal(0)

        issue = issue_registry.async_get_issue(DOMAIN, issue_id)
        expect(issue).to_be_truthy()
        expect(issue.dismissed_version).to_be_truthy()


@test
async def plug_1_push_update_issue_created(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test push update repair issue when device is Shelly Plug 1."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "model", MODEL_PLUG)
        issue_id = PUSH_UPDATE_ISSUE_ID.format(unique=MOCK_MAC)
        expect(await async_setup_component(hass, "repairs", {})).to_be_truthy()
        await hass.async_block_till_done()
        await init_integration(hass, 1, model=MODEL_PLUG)
        await mock_block_device_push_update_failure(hass, mock_block_device)

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)
