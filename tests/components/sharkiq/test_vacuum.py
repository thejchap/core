"""Test the Shark IQ vacuum entity."""

from typing import Any
from unittest.mock import patch

from sharkiq import SharkIqAuthError, SharkIqNotAuthedError, SharkIqVacuum
from tryke import Depends, expect, fixture, test
from voluptuous.error import MultipleInvalid

from homeassistant import exceptions
from homeassistant.components.homeassistant import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.components.sharkiq.const import ATTR_ROOMS, DOMAIN
from homeassistant.components.sharkiq.services import SERVICE_CLEAN_ROOM
from homeassistant.components.sharkiq.vacuum import (
    ATTR_ERROR_CODE,
    ATTR_ERROR_MSG,
    ATTR_LOW_LIGHT,
    ATTR_RECHARGE_RESUME,
    FAN_SPEEDS_MAP,
)
from homeassistant.components.vacuum import (
    ATTR_BATTERY_LEVEL,
    ATTR_FAN_SPEED,
    ATTR_FAN_SPEED_LIST,
    SERVICE_LOCATE,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    SERVICE_STOP,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import MockAyla, MockShark, ROOM_LIST, setup_integration
from .const import ENTRY_ID, SHARK_DEVICE_DICT

from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

VAC_ENTITY_ID = f"vacuum.{SHARK_DEVICE_DICT['product_name'].lower()}"
EXPECTED_FEATURES = (
    VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STATE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.LOCATE
)
FAN_SPEEDS_LIST = list(FAN_SPEEDS_MAP)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@test
async def simple_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that simple properties work as intended."""
    state = hass.states.get(VAC_ENTITY_ID)
    entity = entity_registry.async_get(VAC_ENTITY_ID)

    expect(entity is not None).to_be(True)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(VacuumActivity.CLEANING)
    expect(entity.unique_id).to_equal("AC000Wxxxxxxxxx")


@test.cases(
    test.case("supported_features", attribute=ATTR_SUPPORTED_FEATURES, target_value=EXPECTED_FEATURES),
    test.case("battery_level", attribute=ATTR_BATTERY_LEVEL, target_value=50),
    test.case("fan_speed", attribute=ATTR_FAN_SPEED, target_value="Eco"),
    test.case("fan_speed_list", attribute=ATTR_FAN_SPEED_LIST, target_value=FAN_SPEEDS_LIST),
    test.case("error_code", attribute=ATTR_ERROR_CODE, target_value=7),
    test.case("error_msg", attribute=ATTR_ERROR_MSG, target_value="Cliff sensor is blocked"),
    test.case("low_light", attribute=ATTR_LOW_LIGHT, target_value=False),
    test.case("recharge_resume", attribute=ATTR_RECHARGE_RESUME, target_value=True),
    test.case("rooms", attribute=ATTR_ROOMS, target_value=ROOM_LIST),
)
async def initial_attributes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    attribute: str,
    target_value: Any,
) -> None:
    """Test initial config attributes."""
    state = hass.states.get(VAC_ENTITY_ID)
    expect(state.attributes.get(attribute)).to_equal(target_value)


@test.cases(
    test.case("stop", service=SERVICE_STOP, target_state=VacuumActivity.IDLE),
    test.case("pause", service=SERVICE_PAUSE, target_state=VacuumActivity.PAUSED),
    test.case("return_to_base", service=SERVICE_RETURN_TO_BASE, target_state=VacuumActivity.RETURNING),
    test.case("start", service=SERVICE_START, target_state=VacuumActivity.CLEANING),
)
async def cleaning_states(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    service: str,
    target_state: str,
) -> None:
    """Test cleaning states."""
    service_data = {ATTR_ENTITY_ID: VAC_ENTITY_ID}
    await hass.services.async_call("vacuum", service, service_data, blocking=True)
    state = hass.states.get(VAC_ENTITY_ID)
    expect(state.state).to_equal(target_state)


@test.cases(
    test.case("eco", fan_speed="Eco"),
    test.case("normal", fan_speed="Normal"),
    test.case("max", fan_speed="Max"),
)
async def fan_speed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    fan_speed: str,
) -> None:
    """Test setting fan speeds."""
    service_data = {ATTR_ENTITY_ID: VAC_ENTITY_ID, ATTR_FAN_SPEED: fan_speed}
    await hass.services.async_call(
        "vacuum", SERVICE_SET_FAN_SPEED, service_data, blocking=True
    )
    state = hass.states.get(VAC_ENTITY_ID)
    expect(state.attributes.get(ATTR_FAN_SPEED)).to_equal(fan_speed)


@test.cases(
    test.case("manufacturer", device_property="manufacturer", target_value="Shark"),
    test.case("model", device_property="model", target_value="RV1001AE"),
    test.case("name", device_property="name", target_value="Sharknado"),
    test.case("sw_version", device_property="sw_version", target_value="Dummy Firmware 1.0"),
)
async def device_properties(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    *,
    device_property: str,
    target_value: str,
) -> None:
    """Test device properties."""
    device = device_registry.async_get_device(identifiers={(DOMAIN, "AC000Wxxxxxxxxx")})
    expect(getattr(device, device_property)).to_equal(target_value)


@test.cases(
    test.case(
        "unknown_rooms",
        room_list=["KITCHEN", "MUD_ROOM", "DOG HOUSE"],
        exception=exceptions.ServiceValidationError,
    ),
    test.case(
        "single_unknown_room",
        room_list=["Office"],
        exception=exceptions.ServiceValidationError,
    ),
    test.case("empty", room_list=[], exception=MultipleInvalid),
)
async def clean_room_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    room_list: list,
    exception: type[Exception],
) -> None:
    """Test clean_room errors."""
    data = {ATTR_ENTITY_ID: VAC_ENTITY_ID, ATTR_ROOMS: room_list}

    async with expect_raises_async(exception):
        await hass.services.async_call(DOMAIN, SERVICE_CLEAN_ROOM, data, blocking=True)


@test
async def locate(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
) -> None:
    """Test that the locate command works."""
    with patch.object(SharkIqVacuum, "async_find_device") as mock_locate:
        data = {ATTR_ENTITY_ID: VAC_ENTITY_ID}
        await hass.services.async_call("vacuum", SERVICE_LOCATE, data, blocking=True)
        mock_locate.assert_called_once()


@test.cases(
    test.case("full_list", room_list=["Kitchen", "Living Room"]),
    test.case("single", room_list=["Kitchen"]),
)
async def clean_room(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    room_list: list,
) -> None:
    """Test that the clean_room command works."""
    with patch.object(SharkIqVacuum, "async_clean_rooms") as mock_clean_room:
        data = {ATTR_ENTITY_ID: VAC_ENTITY_ID, ATTR_ROOMS: room_list}
        await hass.services.async_call(DOMAIN, SERVICE_CLEAN_ROOM, data, blocking=True)
        mock_clean_room.assert_called_once_with(room_list)


@test.cases(
    test.case("success", side_effect=None, success=True),
    test.case("auth_error", side_effect=SharkIqAuthError, success=False),
    test.case("not_authed_error", side_effect=SharkIqNotAuthedError, success=False),
    test.case("runtime_error", side_effect=RuntimeError, success=False),
)
async def coordinator_updates(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_integration),
    *,
    side_effect: type[Exception] | None,
    success: bool,
) -> None:
    """Test the update coordinator update functions."""
    entry = hass.config_entries.async_get_entry(ENTRY_ID)
    expect(entry is not None).to_be(True)
    coordinator = entry.runtime_data

    with patch("sharkiq.ayla_api.AylaApi", MockAyla):
        await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})

        with patch.object(
            MockShark, "async_update", side_effect=side_effect
        ) as mock_update:
            data = {ATTR_ENTITY_ID: [VAC_ENTITY_ID]}
            await hass.services.async_call(
                HOMEASSISTANT_DOMAIN, SERVICE_UPDATE_ENTITY, data, blocking=True
            )
            expect(coordinator.last_update_success).to_equal(success)
            mock_update.assert_called_once()

    state = hass.states.get(VAC_ENTITY_ID)
    expect((state.state == STATE_UNAVAILABLE) != success).to_be(True)
