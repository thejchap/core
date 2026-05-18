"""Tests for Shelly light platform (tryke port)."""

from collections.abc import Generator
from contextlib import contextmanager, suppress
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, Mock

from aioshelly.const import (
    MODEL_BULB,
    MODEL_BULB_RGBW,
    MODEL_DIMMER,
    MODEL_DIMMER_2,
    MODEL_DUO,
    MODEL_MULTICOLOR_BULB_G3,
    MODEL_RGBW2,
    MODEL_VINTAGE_V2,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_MAX_COLOR_TEMP_KELVIN,
    ATTR_MIN_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_TRANSITION,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    ColorMode,
    LightEntityFeature,
)
from homeassistant.components.shelly import (
    BLOCK_SLEEPING_PLATFORMS,
    PLATFORMS,
    RPC_SLEEPING_PLATFORMS,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry

from unittest.mock import patch

from tests.components.shelly import (
    get_entity,
    init_integration,
    mutate_rpc_device_status,
    register_device,
    register_entity,
)
from tests.components.shelly._fixtures import (
    mock_block_device as mock_block_device_fixture,
    mock_rpc_device as mock_rpc_device_fixture,
    mock_white_light_set_state,
)
from tests.hass_fixtures import (
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

RELAY_BLOCK_ID = 0
LIGHT_BLOCK_ID = 2
SHELLY_PLUS_RGBW_CHANNELS = 4

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
    with _patch_platforms([Platform.LIGHT]):
        yield


@test
async def block_device_rgbw_bulb(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device RGBW bulb."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        entity_id = "light.test_name"
        await init_integration(hass, 1, model=MODEL_BULB)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((45, 55, 65, 70))
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(48)
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.COLOR_TEMP, ColorMode.RGBW]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            LightEntityFeature.EFFECT
        )
        expect(len(state.attributes[ATTR_EFFECT_LIST])).to_equal(7)
        expect(state.attributes[ATTR_EFFECT]).to_equal("Off")

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="off"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGBW_COLOR: [70, 80, 90, 30],
                ATTR_BRIGHTNESS: 33,
                ATTR_EFFECT: "Flash",
            },
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on",
            gain=13,
            brightness=13,
            red=70,
            green=80,
            blue=90,
            white=30,
            effect=3,
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.RGBW)
        expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((70, 80, 90, 30))
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(33)
        expect(state.attributes[ATTR_EFFECT]).to_equal("Flash")

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 3500},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", temp=3500, mode="white"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.COLOR_TEMP)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(3500)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-light_0")


@test
async def block_device_rgb_bulb(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    caplog: Any = Depends(caplog_fixture),
) -> None:
    """Test block device RGB bulb."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        entity_id = "light.test_name"
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "mode")
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
        )
        await init_integration(hass, 1, model=MODEL_BULB_RGBW)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_RGB_COLOR]).to_equal((45, 55, 65))
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(48)
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.COLOR_TEMP, ColorMode.RGB]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            LightEntityFeature.EFFECT | LightEntityFeature.TRANSITION
        )
        expect(len(state.attributes[ATTR_EFFECT_LIST])).to_equal(4)
        expect(state.attributes[ATTR_EFFECT]).to_equal("Off")

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="off"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGB_COLOR: [70, 80, 90],
                ATTR_BRIGHTNESS: 33,
                ATTR_EFFECT: "Flash",
            },
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", gain=13, brightness=13, red=70, green=80, blue=90, effect=3
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.RGB)
        expect(state.attributes[ATTR_RGB_COLOR]).to_equal((70, 80, 90))
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(33)
        expect(state.attributes[ATTR_EFFECT]).to_equal("Flash")

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 3500},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", temp=3500, mode="white"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.COLOR_TEMP)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(3500)

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "Breath"},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", mode="color"
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_EFFECT]).to_equal("Off")
        expect("Effect 'Breath' not supported" in caplog.text).to_be_truthy()

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-light_1")


@test
async def block_device_white_bulb(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device white bulb."""
    with _patches() as monkeypatch:
        monkeypatch.setitem(mock_block_device.shelly, "num_outputs", 1)
        entity_id = "light.test_name"
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "red")
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "green")
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "blue")
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "mode")
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "colorTemp")
        monkeypatch.delattr(mock_block_device.blocks[LIGHT_BLOCK_ID], "effect")
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
        )
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID],
            "set_state",
            AsyncMock(side_effect=mock_white_light_set_state),
        )
        await init_integration(hass, 1, model=MODEL_VINTAGE_V2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(128)
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.BRIGHTNESS]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            LightEntityFeature.TRANSITION
        )

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="off"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 33},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", gain=13, brightness=13
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(33)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-light_1")


@test.cases(
    test.case("duo", model=MODEL_DUO),
    test.case("bulb_rgbw", model=MODEL_BULB_RGBW),
    test.case("dimmer", model=MODEL_DIMMER),
    test.case("dimmer_2", model=MODEL_DIMMER_2),
    test.case("rgbw2", model=MODEL_RGBW2),
    test.case("vintage_v2", model=MODEL_VINTAGE_V2),
)
async def block_device_support_transition(
    model: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device supports transition."""
    with _patches() as monkeypatch:
        entity_id = "light.test_name_channel_1"
        monkeypatch.setitem(
            mock_block_device.settings, "fw", "20220809-122808/v1.12-g99f7e0b"
        )
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID], "description", "light_1"
        )
        await init_integration(hass, 1, model=model)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(
            bool(
                state.attributes[ATTR_SUPPORTED_FEATURES]
                & LightEntityFeature.TRANSITION
            )
        ).to_be_truthy()

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 4},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="on", transition=4000
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 6},
            blocking=True,
        )
        mock_block_device.blocks[LIGHT_BLOCK_ID].set_state.assert_called_once_with(
            turn="off", transition=5000
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-light_1")


@test
async def block_device_relay_app_type_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test block device relay in app type set to light mode."""
    with _patches() as monkeypatch:
        entity_id = "light.test_name_channel_1"
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "red")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "green")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "blue")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "mode")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "gain")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "brightness")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "effect")
        monkeypatch.delattr(mock_block_device.blocks[RELAY_BLOCK_ID], "colorTemp")
        monkeypatch.setitem(
            mock_block_device.settings["relays"][RELAY_BLOCK_ID],
            "appliance_type",
            "light",
        )
        monkeypatch.setattr(
            mock_block_device.blocks[RELAY_BLOCK_ID], "description", "relay_1"
        )
        await init_integration(hass, 1)

        expect(hass.states.get("switch.test_name_channel_1")).to_equal(None)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.ONOFF]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(0)

        mock_block_device.blocks[RELAY_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_block_device.blocks[RELAY_BLOCK_ID].set_state.assert_called_once_with(
            turn="off"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_block_device.blocks[RELAY_BLOCK_ID].set_state.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_block_device.blocks[RELAY_BLOCK_ID].set_state.assert_called_once_with(
            turn="on"
        )
        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-relay_1")


@test
async def block_device_no_light_blocks(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_block_device: Mock = Depends(mock_block_device_fixture),
) -> None:
    """Test block device without light blocks."""
    with _patches() as monkeypatch:
        monkeypatch.setattr(
            mock_block_device.blocks[LIGHT_BLOCK_ID], "type", "roller"
        )
        await init_integration(hass, 1)

        expect(hass.states.get("light.test_name_channel_1")).to_equal(None)


@test
async def rpc_device_switch_type_lights_mode(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device with switch in consumption type lights mode."""
    with _patches() as monkeypatch:
        entity_id = "light.test_name_test_switch_0"
        monkeypatch.setitem(
            mock_rpc_device.config["sys"]["ui_data"],
            "consumption_types",
            ["lights"],
        )
        monkeypatch.delitem(mock_rpc_device.status, "cover:0")
        await init_integration(hass, 2)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "switch:0", "output", False
        )
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-switch:0")


@test
async def rpc_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC light."""
    with _patches() as monkeypatch:
        entity_id = f"{LIGHT_DOMAIN}.test_light_0"
        monkeypatch.delitem(mock_rpc_device.status, "switch:0")
        await init_integration(hass, 2)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.call_rpc.assert_called_once_with(
            "Light.Set", {"id": 0, "on": True}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(135)

        mock_rpc_device.call_rpc.reset_mock()
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "light:0", "output", False
        )
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.mock_update()
        mock_rpc_device.call_rpc.assert_called_once_with(
            "Light.Set", {"id": 0, "on": False}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 33},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "light:0", "output", True
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "light:0", "brightness", 13
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "Light.Set", {"id": 0, "on": True, "brightness": 13}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(33)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 10.1},
            blocking=True,
        )

        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "Light.Set", {"id": 0, "on": True, "transition_duration": 10.1}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id, ATTR_TRANSITION: 0.4},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "light:0", "output", False
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "Light.Set", {"id": 0, "on": False, "transition_duration": 0.5}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-light:0")


@test
async def rpc_device_rgb_profile(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device in RGB profile."""
    with _patches() as monkeypatch:
        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
        monkeypatch.delitem(mock_rpc_device.status, "rgbw:0")
        entity_id = "light.test_name_test_rgb_0"
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_RGB_COLOR]).to_equal((45, 55, 65))
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.RGB]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            LightEntityFeature.TRANSITION
        )

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: [70, 80, 90]},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgb:0", "rgb", [70, 80, 90]
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGB.Set", {"id": 0, "on": True, "rgb": [70, 80, 90]}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.RGB)
        expect(state.attributes[ATTR_RGB_COLOR]).to_equal((70, 80, 90))

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-rgb:0")


@test
async def rpc_device_rgbw_profile(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC device in RGBW profile."""
    with _patches() as monkeypatch:
        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
        monkeypatch.delitem(mock_rpc_device.status, "rgb:0")
        entity_id = "light.test_name_test_rgbw_0"
        await init_integration(hass, 2)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((21, 22, 23, 120))
        expect(state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
            [ColorMode.RGBW]
        )
        expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
            LightEntityFeature.TRANSITION
        )

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: [72, 82, 92, 128]},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbw:0", "rgb", [72, 82, 92]
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbw:0", "white", 128
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBW.Set", {"id": 0, "on": True, "rgb": [72, 82, 92], "white": 128}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.RGBW)
        expect(state.attributes[ATTR_RGBW_COLOR]).to_equal((72, 82, 92, 128))

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-rgbw:0")


@test
async def rpc_rgbw_device_light_mode_remove_others(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test Shelly RPC RGBW device in light mode removes RGB/RGBW entities."""
    with _patches() as monkeypatch:
        monkeypatch.delitem(mock_rpc_device.status, "rgb:0")
        monkeypatch.delitem(mock_rpc_device.status, "rgbw:0")

        config_entry = await init_integration(hass, 2, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)
        register_entity(
            hass,
            LIGHT_DOMAIN,
            "test_rgb_0",
            "rgb:0",
            config_entry,
            device_id=device_entry.id,
        )
        register_entity(
            hass,
            LIGHT_DOMAIN,
            "test_rgbw_0",
            "rgbw:0",
            config_entry,
            device_id=device_entry.id,
        )

        expect(get_entity(hass, LIGHT_DOMAIN, "rgb:0")).to_be_truthy()
        expect(get_entity(hass, LIGHT_DOMAIN, "rgbw:0")).to_be_truthy()

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            entity_id = f"light.test_light_{i}"

            state = hass.states.get(entity_id)
            expect(state).to_be_truthy()
            expect(state.state).to_equal(STATE_ON)

            entry = entity_registry.async_get(entity_id)
            expect(entry).to_be_truthy()
            expect(entry.unique_id).to_equal(f"123456789ABC-light:{i}")

        expect(get_entity(hass, LIGHT_DOMAIN, "rgb:0")).to_equal(None)
        expect(get_entity(hass, LIGHT_DOMAIN, "rgbw:0")).to_equal(None)


@test.cases(
    test.case("rgb_active", active_mode="rgb", removed_mode="rgbw"),
    test.case("rgbw_active", active_mode="rgbw", removed_mode="rgb"),
)
async def rpc_rgbw_device_rgb_w_modes_remove_others(
    active_mode: str,
    removed_mode: str,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test Shelly RPC RGBW device in RGB/W modes other lights."""
    with _patches() as monkeypatch:
        removed_key = f"{removed_mode}:0"
        config_entry = await init_integration(hass, 2, skip_setup=True)
        device_entry = register_device(device_registry, config_entry)

        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            monkeypatch.delitem(mock_rpc_device.status, f"light:{i}")
            entity_id = f"light.test_name_test_light_{i}"
            register_entity(
                hass,
                LIGHT_DOMAIN,
                entity_id,
                f"light:{i}",
                config_entry,
                device_id=device_entry.id,
            )
        monkeypatch.delitem(mock_rpc_device.status, f"{removed_mode}:0")
        register_entity(
            hass,
            LIGHT_DOMAIN,
            f"test_{removed_key}",
            removed_key,
            config_entry,
            device_id=device_entry.id,
        )

        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            expect(get_entity(hass, LIGHT_DOMAIN, f"light:{i}")).to_be_truthy()
        expect(get_entity(hass, LIGHT_DOMAIN, removed_key)).to_be_truthy()

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        entity_id = f"light.test_name_test_{active_mode}_0"

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal(f"123456789ABC-{active_mode}:0")

        for i in range(SHELLY_PLUS_RGBW_CHANNELS):
            expect(get_entity(hass, LIGHT_DOMAIN, f"light:{i}")).to_equal(None)
        expect(get_entity(hass, LIGHT_DOMAIN, removed_key)).to_equal(None)


@test
async def rpc_cct_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC CCT light."""
    with _patches() as monkeypatch:
        entity_id = f"{LIGHT_DOMAIN}.test_name_cct_light_0"

        config = deepcopy(mock_rpc_device.config)
        config["cct:0"] = {"id": 0, "name": None, "ct_range": [3333, 5555]}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["cct:0"] = {"id": 0, "output": False, "brightness": 77, "ct": 3666}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 2)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-cct:0")

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.call_rpc.assert_called_once_with(
            "CCT.Set", {"id": 0, "on": False}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_rpc_device.call_rpc.reset_mock()
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cct:0", "output", True
        )
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.mock_update()
        mock_rpc_device.call_rpc.assert_called_once_with(
            "CCT.Set", {"id": 0, "on": True}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.COLOR_TEMP)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(196)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(3666)
        expect(state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN]).to_equal(3333)
        expect(state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN]).to_equal(5555)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS_PCT: 88},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cct:0", "brightness", 88
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "CCT.Set", {"id": 0, "on": True, "brightness": 88}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(224)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 4444},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "cct:0", "ct", 4444
        )

        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "CCT.Set", {"id": 0, "on": True, "ct": 4444}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(4444)


@test
async def rpc_remove_cct_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test Shelly RPC remove orphaned CCT light entity."""
    config_entry = await init_integration(hass, 2, skip_setup=True)
    device_entry = register_device(device_registry, config_entry)
    register_entity(
        hass,
        LIGHT_DOMAIN,
        "cct_light_0",
        "cct:0",
        config_entry,
        device_id=device_entry.id,
    )

    expect(get_entity(hass, LIGHT_DOMAIN, "cct:0")).to_be_truthy()

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(get_entity(hass, LIGHT_DOMAIN, "cct:0")).to_equal(None)


@test
async def rpc_cct_light_without_ct_range(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
) -> None:
    """Test RPC CCT light without ct_range in the light config."""
    with _patches() as monkeypatch:
        entity_id = f"{LIGHT_DOMAIN}.living_room_lamp"

        config = deepcopy(mock_rpc_device.config)
        config["cct:0"] = {"id": 0, "name": "Living room lamp"}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["cct:0"] = {"id": 0, "output": False, "brightness": 77, "ct": 3666}
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        expect(state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN]).to_equal(2700)
        expect(state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN]).to_equal(6500)


@test
async def rpc_rgbcct_light(
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(fixture_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rpc_device: Mock = Depends(mock_rpc_device_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test RPC RGBCCT light."""
    with _patches() as monkeypatch:
        entity_id = f"{LIGHT_DOMAIN}.test_name"

        config = deepcopy(mock_rpc_device.config)
        config["rgbcct:0"] = {"id": 0, "name": None}
        monkeypatch.setattr(mock_rpc_device, "config", config)

        status = deepcopy(mock_rpc_device.status)
        status["rgbcct:0"] = {
            "id": 0,
            "output": False,
            "brightness": 44,
            "ct": 3349,
            "rgb": [76, 140, 255],
            "mode": "cct",
        }
        monkeypatch.setattr(mock_rpc_device, "status", status)

        await init_integration(hass, 3, MODEL_MULTICOLOR_BULB_G3)

        entry = entity_registry.async_get(entity_id)
        expect(entry).to_be_truthy()
        expect(entry.unique_id).to_equal("123456789ABC-rgbcct:0")

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBCCT.Set", {"id": 0, "on": False}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_OFF)

        mock_rpc_device.call_rpc.reset_mock()
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbcct:0", "output", True
        )
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBCCT.Set", {"id": 0, "on": True}
        )
        mock_rpc_device.mock_update()

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.COLOR_TEMP)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(112)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(3349)
        expect(state.attributes[ATTR_MIN_COLOR_TEMP_KELVIN]).to_equal(2700)
        expect(state.attributes[ATTR_MAX_COLOR_TEMP_KELVIN]).to_equal(6500)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS_PCT: 88},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbcct:0", "brightness", 88
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBCCT.Set", {"id": 0, "on": True, "brightness": 88}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(224)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_COLOR_TEMP_KELVIN: 4444},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbcct:0", "ct", 4444
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBCCT.Set", {"id": 0, "on": True, "ct": 4444, "mode": "cct"}
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(4444)

        mock_rpc_device.call_rpc.reset_mock()
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: [100, 150, 200]},
            blocking=True,
        )

        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbcct:0", "rgb", [100, 150, 200]
        )
        mutate_rpc_device_status(
            monkeypatch, mock_rpc_device, "rgbcct:0", "mode", "rgb"
        )
        mock_rpc_device.mock_update()

        mock_rpc_device.call_rpc.assert_called_once_with(
            "RGBCCT.Set",
            {"id": 0, "on": True, "rgb": [100, 150, 200], "mode": "rgb"},
        )

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.RGB)
        expect(state.attributes[ATTR_RGB_COLOR]).to_equal((100, 150, 200))
