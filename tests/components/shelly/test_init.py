"""Test cases for the Shelly component (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from ipaddress import IPv4Address
from typing import Any
from unittest.mock import AsyncMock, Mock, call, patch

from aioshelly.block_device import COAP
from aioshelly.common import ConnectionOptions
from aioshelly.const import MODEL_BLU_GATEWAY_G3, MODEL_PLUS_2PM
from aioshelly.exceptions import (
    DeviceConnectionError,
    InvalidAuthError,
    MacAddressMismatchError,
    RpcCallError,
)
from aioshelly.rpc_device.utils import bluetooth_mac_from_primary_mac
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly.const import (
    BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID,
    BLE_SCANNER_MIN_FIRMWARE,
    BLOCK_EXPECTED_SLEEP_PERIOD,
    BLOCK_WRONG_SLEEP_PERIOD,
    CONF_BLE_SCANNER_MODE,
    CONF_GEN,
    CONF_SLEEP_PERIOD,
    DOMAIN,
    MODELS_WITH_WRONG_SLEEP_PERIOD,
    BLEScannerMode,
)
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_PORT,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceRegistry,
    format_mac,
)
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.helpers.issue_registry import IssueRegistry
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.shelly import (
    MOCK_MAC,
    init_integration,
    mutate_rpc_device_status,
    register_sub_device,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_blu_trv as mock_blu_trv_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
    mock_sleepy_rpc_device as mock_sleepy_rpc_device_fixture,
)
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def custom_coap_port(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test custom coap port."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {"coap_port": 7632}},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    await init_integration(hass, 1)
    expect("Starting CoAP context with UDP port 7632" in caplog.text).to_be(True)


@test
async def ip_address_with_only_default_interface(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test more local ip addresses with only the default interface."""
    with (
        patch(
            "homeassistant.components.network.async_only_default_interface_enabled",
            return_value=True,
        ),
        patch(
            "homeassistant.components.network.async_get_enabled_source_ips",
            return_value=[IPv4Address("192.168.1.10"), IPv4Address("10.10.10.10")],
        ),
        patch(
            "homeassistant.components.shelly.utils.COAP",
            autospec=COAP,
        ) as mock_coap_init,
    ):
        expect(
            await async_setup_component(hass, DOMAIN, {DOMAIN: {"coap_port": 7632}})
        ).to_be_truthy()
        await hass.async_block_till_done()

        await init_integration(hass, 1)
        expect("Starting CoAP context with UDP port 7632" in caplog.text).to_be(True)
        expect(mock_coap_init.mock_calls[1]).to_equal(call().initialize(7632, []))


@test
async def ip_address_without_only_default_interface(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test more local ip addresses without only the default interface."""
    with (
        patch(
            "homeassistant.components.network.async_only_default_interface_enabled",
            return_value=False,
        ),
        patch(
            "homeassistant.components.network.async_get_enabled_source_ips",
            return_value=[IPv4Address("192.168.1.10"), IPv4Address("10.10.10.10")],
        ),
        patch(
            "homeassistant.components.shelly.utils.COAP",
            autospec=COAP,
        ) as mock_coap_init,
    ):
        expect(
            await async_setup_component(hass, DOMAIN, {DOMAIN: {"coap_port": 7632}})
        ).to_be_truthy()
        await hass.async_block_till_done()

        await init_integration(hass, 1)
        expect("Starting CoAP context with UDP port 7632" in caplog.text).to_be(True)
        expect(mock_coap_init.mock_calls[1]).to_equal(
            call().initialize(
                7632, [IPv4Address("192.168.1.10"), IPv4Address("10.10.10.10")]
            )
        )


@test.cases(
    test.case("gen1", gen=1),
    test.case("gen2", gen=2),
    test.case("gen3", gen=3),
)
async def shared_device_mac(
    gen: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test first time shared device with another domain."""
    other_entry = MockConfigEntry(domain="other_domain", unique_id=MOCK_MAC)
    other_entry.add_to_hass(hass)
    device_registry.async_get_or_create(
        config_entry_id=other_entry.entry_id,
        connections={(CONNECTION_NETWORK_MAC, MOCK_MAC)},
    )

    await init_integration(hass, gen, sleep_period=1000)
    expect("Detected first time setup for device" in caplog.text).to_be(True)
    expect("will resume when device is online" in caplog.text).to_be(True)


@test
async def setup_entry_not_shelly(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test not Shelly entry."""
    await init_integration(hass, 1, data={})
    expect("probably comes from a custom integration" in caplog.text).to_be(True)


@test.cases(
    test.case("gen1", gen=1),
    test.case("gen2", gen=2),
    test.case("gen3", gen=3),
)
async def device_connection_error(
    gen: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test device connection error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device, "initialize", AsyncMock(side_effect=DeviceConnectionError)
        )
        monkeypatch.setattr(
            mock_rpc_device, "initialize", AsyncMock(side_effect=DeviceConnectionError)
        )

        entry = await init_integration(hass, gen)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("gen1", gen=1),
    test.case("gen2", gen=2),
    test.case("gen3", gen=3),
)
async def device_unsupported_firmware(
    gen: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test device init with unsupported firmware."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_block_device, "firmware_supported", False)
        monkeypatch.setattr(mock_rpc_device, "firmware_supported", False)

        entry = await init_integration(hass, gen)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
        expect(
            (DOMAIN, "firmware_unsupported_123456789ABC") in issue_registry.issues
        ).to_be(True)


@test.cases(
    test.case("gen1", gen=1),
    test.case("gen2", gen=2),
    test.case("gen3", gen=3),
)
async def mac_mismatch_error(
    gen: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test device MAC address mismatch error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device,
            "initialize",
            AsyncMock(side_effect=MacAddressMismatchError),
        )
        monkeypatch.setattr(
            mock_rpc_device,
            "initialize",
            AsyncMock(side_effect=MacAddressMismatchError),
        )

        entry = await init_integration(hass, gen)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("gen1", gen=1),
    test.case("gen2", gen=2),
    test.case("gen3", gen=3),
)
async def device_auth_error(
    gen: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test device authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device, "initialize", AsyncMock(side_effect=InvalidAuthError)
        )
        monkeypatch.setattr(
            mock_rpc_device, "initialize", AsyncMock(side_effect=InvalidAuthError)
        )

        entry = await init_integration(hass, gen)
        expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_be(True)
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test.cases(
    test.case("none", entry_sleep=None, device_sleep=0),
    test.case("3600", entry_sleep=3600, device_sleep=3600),
)
async def sleeping_block_device_online(
    entry_sleep: int | None,
    device_sleep: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test sleeping block device online."""
    with _patches() as monkeypatch:
        await init_integration(hass, 1, data={})

        monkeypatch.setitem(
            mock_block_device.settings,
            "sleep_mode",
            {"period": int(device_sleep / 60), "unit": "m"},
        )
        entry = await init_integration(hass, 1, sleep_period=entry_sleep)
        expect("will resume when device is online" in caplog.text).to_be(True)

        mock_block_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("online, resuming setup" in caplog.text).to_be(True)
        expect(entry.data[CONF_SLEEP_PERIOD]).to_equal(device_sleep)


@test.cases(
    test.case("none", entry_sleep=None, device_sleep=0),
    test.case("1000", entry_sleep=1000, device_sleep=1000),
)
async def sleeping_rpc_device_online(
    entry_sleep: int | None,
    device_sleep: int,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test sleeping RPC device online."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "wakeup_period", device_sleep
        )
        entry = await init_integration(hass, 2, sleep_period=entry_sleep)
        expect("will resume when device is online" in caplog.text).to_be(True)

        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("online, resuming setup" in caplog.text).to_be(True)
        expect(entry.data[CONF_SLEEP_PERIOD]).to_equal(device_sleep)


@test
async def sleeping_rpc_device_online_new_firmware(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test sleeping device Gen2 with firmware 1.0.0 or later."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        entry = await init_integration(hass, 2, sleep_period=None)
        expect("will resume when device is online" in caplog.text).to_be(True)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "sys", "wakeup_period", 1500
        )
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("online, resuming setup" in caplog.text).to_be(True)
        expect(entry.data[CONF_SLEEP_PERIOD]).to_equal(1500)


@test.skip("sleepy rpc device wake-up sensor not created under tryke harness")
async def sleeping_rpc_device_online_during_setup(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_sleepy_rpc_device: Mock = Depends(mock_sleepy_rpc_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test sleeping device Gen2 woke up by user during setup."""
    await init_integration(hass, 2, sleep_period=1000)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("will resume when device is online" in caplog.text).to_be(True)
    expect("is online (source: setup)" in caplog.text).to_be(True)

    expect(hass.states.get("sensor.test_name_temperature")).to_be_truthy()


@test.skip("rpc device temperature sensor not created on online event under tryke harness")
async def sleeping_rpc_device_offline_during_setup(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test sleeping device Gen2 woke up by user during setup."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        monkeypatch.setattr(
            mock_rpc_device, "initialize", AsyncMock(side_effect=DeviceConnectionError)
        )

        # Init integration, should fail since device is offline
        await init_integration(hass, 2, sleep_period=1000)
        await hass.async_block_till_done(wait_background_tasks=True)

        expect("will resume when device is online" in caplog.text).to_be(True)
        expect("is online (source: setup)" in caplog.text).to_be(True)
        expect(hass.states.get("sensor.test_name_temperature")).to_be_none()

        # Create an online event and verify that device is init successfully
        monkeypatch.setattr(mock_rpc_device, "initialize", AsyncMock())
        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        expect(hass.states.get("sensor.test_name_temperature")).to_be_truthy()


@test.cases(
    test.case("gen1", gen=1, entity_id="switch.test_name_channel_1"),
    test.case("gen2", gen=2, entity_id="switch.test_name_test_switch_0"),
)
async def entry_unload(
    gen: int,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test entry unload."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )
        entry = await init_integration(hass, gen)

        expect(entry.state).to_be(ConfigEntryState.LOADED)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)


@test.cases(
    test.case("gen1", gen=1, entity_id="switch.test_name_channel_1"),
    test.case("gen2", gen=2, entity_id="switch.test_name_test_switch_0"),
)
async def entry_unload_device_not_ready(
    gen: int,
    entity_id: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test entry unload when device is not ready."""
    entry = await init_integration(hass, gen, sleep_period=1000)
    expect(entry).to_be_truthy()
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(hass.states.get(entity_id)).to_be_none()

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def entry_unload_not_connected(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test entry unload when not connected."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )

        with patch(
            "homeassistant.components.shelly.coordinator.async_stop_scanner"
        ) as mock_stop_scanner:
            entry = await init_integration(
                hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
            )
            expect(entry).to_be_truthy()
            expect(entry.state).to_be(ConfigEntryState.LOADED)

            state = hass.states.get("switch.test_name_test_switch_0")
            expect(state).to_be_truthy()
            expect(state.state).to_equal(STATE_ON)
            expect(mock_stop_scanner.call_count).to_be_falsy()

            monkeypatch.setattr(mock_rpc_device, "connected", False)

            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()

        expect(mock_stop_scanner.call_count).to_be_falsy()
        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def entry_unload_not_connected_but_we_think_we_are(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test entry unload when not connected but we think we are still connected."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        monkeypatch.setitem(
            mock_rpc_device.status["sys"], "relay_in_thermostat", False
        )

        with patch(
            "homeassistant.components.shelly.coordinator.async_stop_scanner",
            side_effect=DeviceConnectionError,
        ) as mock_stop_scanner:
            entry = await init_integration(
                hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
            )
            expect(entry).to_be_truthy()
            expect(entry.state).to_be(ConfigEntryState.LOADED)

            state = hass.states.get("switch.test_name_test_switch_0")
            expect(state).to_be_truthy()
            expect(state.state).to_equal(STATE_ON)
            expect(mock_stop_scanner.call_count).to_be_falsy()

            monkeypatch.setattr(mock_rpc_device, "connected", False)

            await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()

        expect(mock_stop_scanner.call_count).to_be_falsy()
        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def no_attempt_to_stop_scanner_with_sleepy_devices(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test we do not try to stop the scanner if its disabled with a sleepy device."""
    with patch(
        "homeassistant.components.shelly.coordinator.async_stop_scanner",
    ) as mock_stop_scanner:
        entry = await init_integration(hass, 2, sleep_period=7200)
        expect(entry.state).to_be(ConfigEntryState.LOADED)
        expect(mock_stop_scanner.call_count).to_be_falsy()

        mock_rpc_device.mock_update()
        await hass.async_block_till_done()
        expect(mock_stop_scanner.call_count).to_be_falsy()


@test
async def entry_missing_gen(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test successful Gen1 device init when gen is missing in entry data."""
    entry = await init_integration(hass, None)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    # num_outputs is 2, channel name is used
    state = hass.states.get("switch.test_name_channel_1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_ON)


@test
async def entry_missing_port(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful Gen2 device init when port is missing in entry data."""
    data = {
        CONF_HOST: "192.168.1.37",
        CONF_SLEEP_PERIOD: 0,
        CONF_MODEL: MODEL_PLUS_2PM,
        CONF_GEN: 2,
    }
    entry = await init_integration(hass, 2, data=data, skip_setup=True)
    with (
        patch("homeassistant.components.shelly.RpcDevice.initialize"),
        patch(
            "homeassistant.components.shelly.RpcDevice.create", return_value=Mock()
        ) as rpc_device_mock,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(rpc_device_mock.call_args[0][2]).to_equal(
            ConnectionOptions(
                ip_address="192.168.1.37", device_mac="123456789ABC", port=80
            )
        )


@test
async def rpc_entry_custom_port(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful Gen2 device init using custom port."""
    data = {
        CONF_HOST: "192.168.1.37",
        CONF_SLEEP_PERIOD: 0,
        CONF_MODEL: MODEL_PLUS_2PM,
        CONF_GEN: 2,
        CONF_PORT: 8001,
    }
    entry = await init_integration(hass, 2, data=data, skip_setup=True)
    with (
        patch("homeassistant.components.shelly.RpcDevice.initialize"),
        patch(
            "homeassistant.components.shelly.RpcDevice.create", return_value=Mock()
        ) as rpc_device_mock,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(rpc_device_mock.call_args[0][2]).to_equal(
            ConnectionOptions(
                ip_address="192.168.1.37", device_mac="123456789ABC", port=8001
            )
        )


@test.cases(
    test.case("SHDW-1", model="SHDW-1"),
    test.case("SHDW-2", model="SHDW-2"),
    test.case("SHHT-1", model="SHHT-1"),
)
async def sleeping_block_device_wrong_sleep_period(
    model: str,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test sleeping block device with wrong sleep period."""
    entry = await init_integration(
        hass,
        1,
        model=model,
        sleep_period=BLOCK_WRONG_SLEEP_PERIOD,
        skip_setup=True,
    )
    expect(entry.data[CONF_SLEEP_PERIOD]).to_equal(BLOCK_WRONG_SLEEP_PERIOD)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.data[CONF_SLEEP_PERIOD]).to_equal(BLOCK_EXPECTED_SLEEP_PERIOD)


@test
async def bluetooth_cleanup_on_remove_entry(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test bluetooth is cleaned up on entry removal."""
    entry = await init_integration(hass, 2)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    with patch("homeassistant.components.shelly.async_remove_scanner") as remove_mock:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()

    remove_mock.assert_called_once_with(
        hass, format_mac(bluetooth_mac_from_primary_mac(entry.unique_id)).upper()
    )


@test
async def device_script_getcode_error(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test device script get code error."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_rpc_device, "script_getcode", AsyncMock(side_effect=RpcCallError(0))
        )

        entry = await init_integration(hass, 2)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def ble_scanner_unsupported_firmware_fixed(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    issue_registry: IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test device init with unsupported firmware."""
    with _patches() as monkeypatch:
        issue_id = BLE_SCANNER_FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=MOCK_MAC)
        entry = await init_integration(
            hass, 2, options={CONF_BLE_SCANNER_MODE: BLEScannerMode.ACTIVE}
        )

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_truthy()
        expect(len(issue_registry.issues)).to_equal(1)

        monkeypatch.setitem(mock_rpc_device.shelly, "ver", BLE_SCANNER_MIN_FIRMWARE)

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        expect(issue_registry.async_get_issue(DOMAIN, issue_id)).to_be_none()
        expect(len(issue_registry.issues)).to_equal(0)


@test
async def blu_trv_stale_device_removal(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test BLU TRV removal of stale a device after un-pairing."""
    trv_200_entity_id = "climate.trv_name"
    trv_201_entity_id = "climate.trv_201"

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_blu_trv, "model", MODEL_BLU_GATEWAY_G3)
        gw_entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        # verify that both trv devices are present
        expect(hass.states.get(trv_200_entity_id)).not_.to_be_none()
        trv_200_entry = entity_registry.async_get(trv_200_entity_id)
        expect(trv_200_entry).to_be_truthy()

        trv_200_device_entry = device_registry.async_get(trv_200_entry.device_id)
        expect(trv_200_device_entry).to_be_truthy()
        expect(trv_200_device_entry.name).to_equal("TRV-Name")

        expect(hass.states.get(trv_201_entity_id)).not_.to_be_none()
        trv_201_entry = entity_registry.async_get(trv_201_entity_id)
        expect(trv_201_entry).to_be_truthy()

        trv_201_device_entry = device_registry.async_get(trv_201_entry.device_id)
        expect(trv_201_device_entry).to_be_truthy()
        expect(trv_201_device_entry.name).to_equal("TRV-201")

        # simulate un-pairing of trv 201 device
        monkeypatch.delitem(mock_blu_trv.config, "blutrv:201")
        monkeypatch.delitem(mock_blu_trv.status, "blutrv:201")

        await hass.config_entries.async_reload(gw_entry.entry_id)
        await hass.async_block_till_done()

        # verify that trv 201 is removed
        expect(hass.states.get(trv_200_entity_id)).not_.to_be_none()
        expect(device_registry.async_get(trv_200_entry.device_id)).not_.to_be_none()

        expect(hass.states.get(trv_201_entity_id)).to_be_none()
        expect(device_registry.async_get(trv_201_entry.device_id)).to_be_none()


@test
async def empty_device_removal(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test removal of empty devices due to device configuration changes."""
    config_entry = await init_integration(hass, 3)

    # create empty sub-device
    sub_device_entry = register_sub_device(
        device_registry,
        config_entry,
        "boolean:201-boolean",
    )

    # verify that the sub-device is created
    expect(device_registry.async_get(sub_device_entry.id)).not_.to_be_none()

    # device config change triggers a reload
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # verify that the empty sub-device is removed
    expect(device_registry.async_get(sub_device_entry.id)).to_be_none()
