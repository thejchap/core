"""Tests for the Bond fan device."""

from datetime import timedelta
from unittest.mock import call

from bond_async import Action, DeviceType, Direction
from tryke import Depends, expect, fixture, test

from homeassistant import core
from homeassistant.components import fan
from homeassistant.components.bond.const import DOMAIN
from homeassistant.components.bond.fan import PRESET_MODE_BREEZE
from homeassistant.components.bond.services import SERVICE_SET_FAN_SPEED_TRACKED_STATE
from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_DIRECTION,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
    FanEntityFeature,
    NotValidPresetModeError,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import utcnow

from .common import (
    ceiling_fan,
    help_test_entity_available,
    patch_bond_action,
    patch_bond_action_returns_clientresponseerror,
    patch_bond_device_state,
    setup_platform,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


def ceiling_fan_with_breeze(name: str):
    """Create a ceiling fan with given name with breeze support."""
    return {
        "name": name,
        "type": DeviceType.CEILING_FAN,
        "actions": ["SetSpeed", "SetDirection", "BreezeOn"],
    }


async def turn_fan_on(
    hass: core.HomeAssistant,
    fan_id: str,
    percentage: int | None = None,
    preset_mode: str | None = None,
) -> None:
    """Turn the fan on at the specified speed."""
    service_data = {ATTR_ENTITY_ID: fan_id}
    if preset_mode:
        service_data[fan.ATTR_PRESET_MODE] = preset_mode
    if percentage is not None:
        service_data[fan.ATTR_PERCENTAGE] = percentage
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        service_data=service_data,
        blocking=True,
    )
    await hass.async_block_till_done()


@test
async def entity_registry_test(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_version={"bondid": "test-hub-id"},
        bond_device_id="test-device-id",
    )

    entity = entity_registry.entities["fan.name_1"]
    expect(entity.unique_id).to_equal("test-hub-id_test-device-id")

    device = device_registry.async_get(entity.device_id)
    expect(device.configuration_url).to_equal("http://some host")


@test
async def non_standard_speed_list(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that the device is registered with custom speed list if number of supported speeds differs form 3."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        props={"max_speed": 6},
    )

    with patch_bond_device_state():
        with patch_bond_action() as mock_set_speed_low:
            await turn_fan_on(hass, "fan.name_1", percentage=100 / 6 * 2)
        mock_set_speed_low.assert_called_once_with(
            "test-device-id", Action.set_speed(2)
        )

        with patch_bond_action() as mock_set_speed_medium:
            await turn_fan_on(hass, "fan.name_1", percentage=100 / 6 * 4)
        mock_set_speed_medium.assert_called_once_with(
            "test-device-id", Action.set_speed(4)
        )

        with patch_bond_action() as mock_set_speed_high:
            await turn_fan_on(hass, "fan.name_1", percentage=100)
        mock_set_speed_high.assert_called_once_with(
            "test-device-id", Action.set_speed(6)
        )


@test
async def fan_speed_with_no_max_speed(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that fans without max speed (increase/decrease controls) map speed to HA standard."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        props={"no": "max_speed"},
        state={"power": 1, "speed": 14},
    )

    expect(hass.states.get("fan.name_1").attributes["percentage"]).to_equal(100)


@test
async def turn_on_fan_with_speed(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn on command delegates to set speed API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=1)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(1))


@test
async def turn_on_fan_with_percentage_3_speeds(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn on command delegates to set speed API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=10)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(1))

    mock_set_speed.reset_mock()
    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=50)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(2))

    mock_set_speed.reset_mock()
    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=100)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(3))


@test
async def turn_on_fan_with_percentage_6_speeds(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn on command delegates to set speed API."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        props={"max_speed": 6},
    )

    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=10)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(1))

    mock_set_speed.reset_mock()
    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=50)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(3))

    mock_set_speed.reset_mock()
    with patch_bond_action() as mock_set_speed, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=100)

    mock_set_speed.assert_called_with("test-device-id", Action.set_speed(6))


@test
async def turn_on_fan_preset_mode(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn on command delegates to breeze on API."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan_with_breeze("name-1"),
        bond_device_id="test-device-id",
        props={"max_speed": 6},
    )
    state = hass.states.get("fan.name_1")
    expect(state.attributes[ATTR_PRESET_MODES]).to_equal([PRESET_MODE_BREEZE])
    expect(
        bool(state.attributes[ATTR_SUPPORTED_FEATURES] & FanEntityFeature.PRESET_MODE)
    ).to_be(True)

    with patch_bond_action() as mock_set_preset_mode, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", preset_mode=PRESET_MODE_BREEZE)

    mock_set_preset_mode.assert_called_with("test-device-id", Action(Action.BREEZE_ON))

    with patch_bond_action() as mock_set_preset_mode, patch_bond_device_state():
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            service_data={
                ATTR_PRESET_MODE: PRESET_MODE_BREEZE,
                ATTR_ENTITY_ID: "fan.name_1",
            },
            blocking=True,
        )

    mock_set_preset_mode.assert_called_with("test-device-id", Action(Action.BREEZE_ON))


@test
async def turn_on_fan_preset_mode_not_supported(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests calling breeze mode on a fan that does not support it raises."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        props={"max_speed": 6},
    )

    with patch_bond_action(), patch_bond_device_state():
        async with expect_raises_async(NotValidPresetModeError):
            await turn_fan_on(hass, "fan.name_1", preset_mode=PRESET_MODE_BREEZE)

    with patch_bond_action(), patch_bond_device_state():
        async with expect_raises_async(NotValidPresetModeError):
            await hass.services.async_call(
                FAN_DOMAIN,
                SERVICE_SET_PRESET_MODE,
                service_data={
                    ATTR_PRESET_MODE: PRESET_MODE_BREEZE,
                    ATTR_ENTITY_ID: "fan.name_1",
                },
                blocking=True,
            )


@test
async def turn_on_fan_with_off_with_breeze(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn off command delegates to turn off API."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan_with_breeze("name-1"),
        bond_device_id="test-device-id",
        state={"breeze": [1, 0, 0]},
    )

    expect(hass.states.get("fan.name_1").attributes[ATTR_PRESET_MODE]).to_equal(
        PRESET_MODE_BREEZE
    )

    with patch_bond_action() as mock_actions, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=0)

    expect(mock_actions.mock_calls).to_equal(
        [
            call("test-device-id", Action(Action.BREEZE_OFF)),
            call("test-device-id", Action.turn_off()),
        ]
    )


@test
async def turn_on_fan_without_speed(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn on command delegates to turn on API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_on, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1")

    mock_turn_on.assert_called_with("test-device-id", Action.turn_on())


@test
async def turn_on_fan_with_off_percentage(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn off command delegates to turn off API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_off, patch_bond_device_state():
        await turn_fan_on(hass, "fan.name_1", percentage=0)

    mock_turn_off.assert_called_with("test-device-id", Action.turn_off())


@test
async def set_speed_off(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that set_speed(off) command delegates to turn off API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_off, patch_bond_device_state():
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            service_data={ATTR_ENTITY_ID: "fan.name_1", ATTR_PERCENTAGE: 0},
            blocking=True,
        )
    await hass.async_block_till_done()

    mock_turn_off.assert_called_with("test-device-id", Action.turn_off())


@test
async def turn_off_fan(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that turn off command delegates to API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_turn_off, patch_bond_device_state():
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "fan.name_1"},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_turn_off.assert_called_once_with("test-device-id", Action.turn_off())


@test
async def set_speed_belief_speed_zero(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that set power belief service delegates to API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_action, patch_bond_device_state():
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_SPEED_TRACKED_STATE,
            {ATTR_ENTITY_ID: "fan.name_1", "speed": 0},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_action.assert_called_once_with(
        "test-device-id", Action.set_power_state_belief(False)
    )


@test
async def set_speed_belief_speed_api_error(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that set power belief service delegates to API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with (
        patch_bond_action_returns_clientresponseerror(),
        patch_bond_device_state(),
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_SET_FAN_SPEED_TRACKED_STATE,
                {ATTR_ENTITY_ID: "fan.name_1", "speed": 100},
                blocking=True,
            )


@test
async def set_speed_belief_speed_100(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that set power belief service delegates to API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_action, patch_bond_device_state():
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_SPEED_TRACKED_STATE,
            {ATTR_ENTITY_ID: "fan.name_1", "speed": 100},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_action.assert_any_call("test-device-id", Action.set_power_state_belief(True))
    mock_action.assert_called_with("test-device-id", Action.set_speed_belief(3))


@test
async def update_reports_fan_on(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that update command sets correct state when Bond API reports fan power is on."""
    await setup_platform(hass, FAN_DOMAIN, ceiling_fan("name-1"))

    with patch_bond_device_state(return_value={"power": 1, "speed": 1}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("fan.name_1").state).to_equal("on")


@test
async def update_reports_fan_off(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that update command sets correct state when Bond API reports fan power is off."""
    await setup_platform(hass, FAN_DOMAIN, ceiling_fan("name-1"))

    with patch_bond_device_state(return_value={"power": 0, "speed": 1}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("fan.name_1").state).to_equal("off")


@test
async def update_reports_direction_forward(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that update command sets correct direction when Bond API reports fan direction is forward."""
    await setup_platform(hass, FAN_DOMAIN, ceiling_fan("name-1"))

    with patch_bond_device_state(return_value={"direction": Direction.FORWARD}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("fan.name_1").attributes[ATTR_DIRECTION]).to_equal(
        DIRECTION_FORWARD
    )


@test
async def update_reports_direction_reverse(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that update command sets correct direction when Bond API reports fan direction is reverse."""
    await setup_platform(hass, FAN_DOMAIN, ceiling_fan("name-1"))

    with patch_bond_device_state(return_value={"direction": Direction.REVERSE}):
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=30))
        await hass.async_block_till_done()

    expect(hass.states.get("fan.name_1").attributes[ATTR_DIRECTION]).to_equal(
        DIRECTION_REVERSE
    )


@test
async def set_fan_direction(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that set direction command delegates to API."""
    await setup_platform(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), bond_device_id="test-device-id"
    )

    with patch_bond_action() as mock_set_direction, patch_bond_device_state():
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_DIRECTION,
            {ATTR_ENTITY_ID: "fan.name_1", ATTR_DIRECTION: DIRECTION_FORWARD},
            blocking=True,
        )
        await hass.async_block_till_done()

    mock_set_direction.assert_called_once_with(
        "test-device-id", Action.set_direction(Direction.FORWARD)
    )


@test
async def fan_available(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Tests that available state is updated based on API errors."""
    await help_test_entity_available(
        hass, FAN_DOMAIN, ceiling_fan("name-1"), "fan.name_1"
    )


@test
async def setup_smart_by_bond_fan(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test setting up a fan without a hub."""
    config_entry = await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_device_id="test-device-id",
        bond_version={
            "bondid": "KXXX12345",
            "target": "test-model",
            "fw_ver": "test-version",
            "mcu_ver": "test-hw-version",
        },
    )
    expect(hass.states.get("fan.name_1") is not None).to_be(True)
    entry = entity_registry.async_get("fan.name_1")
    expect(entry.device_id is not None).to_be(True)
    device = device_registry.async_get(entry.device_id)
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("test-version")
    expect(device.manufacturer).to_equal("Olibra")
    expect(device.identifiers).to_equal({("bond", "KXXX12345", "test-device-id")})
    expect(device.hw_version).to_equal("test-hw-version")
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()


@test
async def setup_hub_template_fan(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test setting up a fan on a hub created from a template."""
    config_entry = await setup_platform(
        hass,
        FAN_DOMAIN,
        {**ceiling_fan("name-1"), "template": "test-template"},
        bond_device_id="test-device-id",
        props={"branding_profile": "test-branding-profile"},
        bond_version={
            "bondid": "ZXXX12345",
            "target": "test-model",
            "fw_ver": "test-version",
            "mcu_ver": "test-hw-version",
        },
    )
    expect(hass.states.get("fan.name_1") is not None).to_be(True)
    entry = entity_registry.async_get("fan.name_1")
    expect(entry.device_id is not None).to_be(True)
    device = device_registry.async_get(entry.device_id)
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_be_none()
    expect(device.model).to_equal("test-branding-profile test-template")
    expect(device.manufacturer).to_equal("Olibra")
    expect(device.identifiers).to_equal({("bond", "ZXXX12345", "test-device-id")})
    expect(device.hw_version).to_be_none()
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
