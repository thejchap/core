"""Tests for Shelly button platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioshelly.const import MODEL_BLU_GATEWAY_G3, MODEL_PLUS_SMOKE, MODEL_WALL_DISPLAY
from aioshelly.exceptions import DeviceConnectionError, InvalidAuthError, RpcCallError
from tryke import Depends, expect, fixture, test

from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.shelly.const import DOMAIN, MODEL_FRANKEVER_WATER_VALVE
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from tests.components.shelly import (
    MOCK_MAC,
    init_integration,
    mutate_rpc_device_status,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_blu_trv as mock_blu_trv_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
)
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

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


@contextmanager
def _patch_platforms(platforms: list[Platform]) -> Generator[None]:
    """Only allow given platforms to be loaded."""
    with (
        patch(
            "homeassistant.components.shelly.PLATFORMS",
            list(set(PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.BLOCK_SLEEPING_PLATFORMS",
            list(set(BLOCK_SLEEPING_PLATFORMS) & set(platforms)),
        ),
        patch(
            "homeassistant.components.shelly.RPC_SLEEPING_PLATFORMS",
            list(set(RPC_SLEEPING_PLATFORMS) & set(platforms)),
        ),
    ):
        yield


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@fixture
def fixture_platforms() -> Generator[None]:
    """Limit platforms under test."""
    with _patch_platforms([Platform.BUTTON]):
        yield


@test
async def block_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device reboot button."""
    await init_integration(hass, 1)

    entity_id = "button.test_name_restart"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-reboot")

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(mock_block_device.trigger_reboot.call_count).to_equal(1)


@test
async def rpc_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test rpc device reboot button (snapshot assertions dropped)."""
    await init_integration(hass, 2)

    entity_id = "button.test_name_restart"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()
    expect(entry.unique_id).to_equal("123456789ABC-reboot")

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(mock_rpc_device.trigger_reboot.call_count).to_equal(1)


@test.cases(
    test.case(
        "device_connection",
        exc_id="device_connection",
        error="Device communication error occurred while calling action for button.test_name_restart of Test name",
    ),
    test.case(
        "rpc_call",
        exc_id="rpc_call",
        error="RPC call error occurred while calling action for button.test_name_restart of Test name",
    ),
)
async def rpc_button_exc(
    exc_id: str,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC button with exception."""
    await init_integration(hass, 2)

    if exc_id == "device_connection":
        exception: Exception | type[Exception] = DeviceConnectionError
    else:
        exception = RpcCallError(999)

    mock_rpc_device.trigger_reboot.side_effect = exception

    async with expect_raises_async(HomeAssistantError, match=error):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.test_name_restart"},
            blocking=True,
        )


@test
async def rpc_button_reauth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test rpc device reboot button with authentication error."""
    entry = await init_integration(hass, 2)

    mock_rpc_device.trigger_reboot.side_effect = InvalidAuthError

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.test_name_restart"},
        blocking=True,
    )

    expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be_truthy()
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test.cases(
    test.case("gen2_old", gen=2, old_unique_id="123456789ABC_reboot", new_unique_id="123456789ABC-reboot", migration=True),
    test.case("gen1_old", gen=1, old_unique_id="123456789ABC_reboot", new_unique_id="123456789ABC-reboot", migration=True),
    test.case("gen2_already_new", gen=2, old_unique_id="123456789ABC-reboot", new_unique_id="123456789ABC-reboot", migration=False),
)
async def migrate_unique_id(
    gen: int,
    old_unique_id: str,
    new_unique_id: str,
    migration: bool,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test migration of unique_id."""
    entry = await init_integration(hass, gen, skip_setup=True)

    entity = entity_registry.async_get_or_create(
        suggested_object_id="test_name_restart",
        disabled_by=None,
        domain=BUTTON_DOMAIN,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    expect(entity.unique_id).to_equal(old_unique_id)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get("button.test_name_restart")
    expect(entity_entry).to_be_truthy()
    expect(entity_entry.unique_id).to_equal(new_unique_id)

    expect(
        bool("Migrating unique_id for button.test_name_restart" in caplog.text)
        == migration
    ).to_be_truthy()


@test
async def rpc_blu_trv_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC BLU TRV button (snapshot assertions dropped)."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_blu_trv.status, "script:1")
        monkeypatch.delitem(mock_blu_trv.status, "script:2")
        monkeypatch.delitem(mock_blu_trv.status, "script:3")

        await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        entity_id = "button.trv_name_calibrate"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_blu_trv.trigger_blu_trv_calibration.assert_called_once_with(200)


@test.cases(
    test.case(
        "device_connection",
        exc_id="device_connection",
        error="Device communication error occurred while calling action for button.trv_name_calibrate of Test name",
    ),
    test.case(
        "rpc_call",
        exc_id="rpc_call",
        error="RPC call error occurred while calling action for button.trv_name_calibrate of Test name",
    ),
)
async def rpc_blu_trv_button_exc(
    exc_id: str,
    error: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test RPC BLU TRV button with exception."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_blu_trv.status, "script:1")
        monkeypatch.delitem(mock_blu_trv.status, "script:2")
        monkeypatch.delitem(mock_blu_trv.status, "script:3")

        await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        if exc_id == "device_connection":
            exception: Exception | type[Exception] = DeviceConnectionError
        else:
            exception = RpcCallError(999)

        mock_blu_trv.trigger_blu_trv_calibration.side_effect = exception

        async with expect_raises_async(HomeAssistantError, match=error):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {ATTR_ENTITY_ID: "button.trv_name_calibrate"},
                blocking=True,
            )


@test
async def rpc_blu_trv_button_auth_error(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
) -> None:
    """Test RPC BLU TRV button with authentication error."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_blu_trv.status, "script:1")
        monkeypatch.delitem(mock_blu_trv.status, "script:2")
        monkeypatch.delitem(mock_blu_trv.status, "script:3")

        entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

        mock_blu_trv.trigger_blu_trv_calibration.side_effect = InvalidAuthError

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.trv_name_calibrate"},
            blocking=True,
        )

        expect(entry.state is ConfigEntryState.LOADED).to_be_truthy()

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)

        flow = flows[0]
        expect(flow.get("step_id")).to_equal("reauth_confirm")
        expect(flow.get("handler")).to_equal(DOMAIN)

        expect("context" in flow).to_be_truthy()
        expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
        expect(flow["context"].get("entry_id")).to_equal(entry.entry_id)


@test
async def rpc_device_virtual_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a virtual button for RPC device (snapshot assertions dropped)."""
    config = deepcopy(mock_rpc_device.config)
    config["button:200"] = {
        "name": "Button",
        "meta": {"ui": {"view": "button"}},
    }
    status = deepcopy(mock_rpc_device.status)
    status["button:200"] = {"value": None}

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "config", config)
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)
        entity_id = "button.test_name_button"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.button_trigger.assert_called_once_with(200, "single_push")


@test
async def rpc_remove_virtual_button_when_orphaned(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Check whether the virtual button will be removed if it has been removed from the device configuration."""
    config_entry = await init_integration(hass, 3, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        BUTTON_DOMAIN,
        "test_name_button_200",
        "button:200",
        config_entry,
        device_id=device_entry.id,
    )

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_none()


@test
async def wall_display_virtual_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a Wall Display virtual button (snapshot assertions dropped)."""
    config = deepcopy(mock_rpc_device.config)
    config["button:200"] = {"name": "Button"}
    status = deepcopy(mock_rpc_device.status)
    status["button:200"] = {"value": None}

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "config", config)
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)
        entity_id = "button.test_name_button"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.button_trigger.assert_called_once_with(200, "single_push")


@test
async def migrate_unique_id_blu_trv(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_blu_trv: Mock = Depends(mock_blu_trv_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test migration of unique_id for BLU TRV button."""
    entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3, skip_setup=True)

    old_unique_id = "f8:44:77:25:f0:dd_calibrate"

    entity = entity_registry.async_get_or_create(
        suggested_object_id="trv_name_calibrate",
        disabled_by=None,
        domain=BUTTON_DOMAIN,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    expect(entity.unique_id).to_equal(old_unique_id)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get("button.trv_name_calibrate")
    expect(entity_entry).to_be_truthy()
    expect(entity_entry.unique_id).to_equal("F8447725F0DD-blutrv:200-calibrate")

    expect("Migrating unique_id for button.trv_name_calibrate" in caplog.text).to_be_truthy()


@test.cases(
    test.case("generic", old_id="button", new_id="button_generic", role=None),
    test.case("open", old_id="button", new_id="button_open", role="open"),
    test.case("close", old_id="button", new_id="button_close", role="close"),
)
async def migrate_unique_id_virtual_components_roles(
    old_id: str,
    new_id: str,
    role: str | None,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test migration of unique_id for virtual components to include role."""
    entry = await init_integration(
        hass, 3, model=MODEL_FRANKEVER_WATER_VALVE, skip_setup=True
    )
    old_unique_id = f"{MOCK_MAC}-{old_id}:200"
    new_unique_id = f"{old_unique_id}-{new_id}"
    config = deepcopy(mock_rpc_device.config)
    if role:
        config[f"{old_id}:200"] = {"role": role}
    else:
        config[f"{old_id}:200"] = {}

    with _patches() as monkeypatch:
        monkeypatch.setattr(mock_rpc_device, "config", config)

        entity = entity_registry.async_get_or_create(
            suggested_object_id="test_name_test_button",
            disabled_by=None,
            domain=BUTTON_DOMAIN,
            platform=DOMAIN,
            unique_id=old_unique_id,
            config_entry=entry,
        )
        expect(entity.unique_id).to_equal(old_unique_id)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_entry = entity_registry.async_get("button.test_name_test_button")
        expect(entity_entry).to_be_truthy()
        expect(entity_entry.unique_id).to_equal(new_unique_id)

        expect(
            "Migrating unique_id for button.test_name_test_button" in caplog.text
        ).to_be_truthy()


@test
async def rpc_smoke_mute_alarm_button(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC smoke mute alarm button."""
    entity_id = f"{BUTTON_DOMAIN}.test_name_mute_alarm"

    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
        monkeypatch.setattr(
            mock_rpc_device, "config", {"smoke:0": {"id": 0, "name": None}}
        )
        monkeypatch.setattr(mock_rpc_device, "connected", False)
        with patch.object(
            mock_rpc_device,
            "initialize",
            new_callable=AsyncMock,
            side_effect=DeviceConnectionError,
        ):
            await init_integration(hass, 2, sleep_period=1000, model=MODEL_PLUS_SMOKE)

        expect(hass.states.get(entity_id)).to_be_none()

        mock_rpc_device.mock_online()
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)

        # mutate_rpc_device_status uses pytest.MonkeyPatch.setattr; emulate it via _patches
        new_status = deepcopy(mock_rpc_device.status)
        new_status["smoke:0"]["alarm"] = True
        monkeypatch.setattr(mock_rpc_device, "status", new_status)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNKNOWN)

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()
        mock_rpc_device.smoke_mute_alarm.assert_called_once_with(0)

        monkeypatch.setattr(mock_rpc_device, "initialized", False)
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_UNAVAILABLE)


@test.cases(
    test.case("turn_on", action="turn_on", value=True),
    test.case("turn_off", action="turn_off", value=False),
)
async def wall_display_screen_buttons(
    action: str,
    value: bool,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test a Wall Display screen buttons (snapshot assertions dropped)."""
    await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)
    entity_id = f"button.test_name_{action}_the_screen"

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()

    entry = entity_registry.async_get(entity_id)
    expect(entry).to_be_truthy()

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    mock_rpc_device.wall_display_set_screen.assert_called_once_with(value=value)


@test
async def rpc_remove_restart_button_for_sleeping_devices(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC remove restart button for sleeping devices."""
    config_entry = await init_integration(hass, 2, sleep_period=1000, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    entity_id = register_entity(
        hass,
        BUTTON_DOMAIN,
        "test_name_restart",
        "reboot",
        config_entry,
        device_id=device_entry.id,
    )

    expect(entity_registry.async_get(entity_id)).to_be_truthy()

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(entity_id)).to_be_none()
