"""Tests for fan platforms."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.fan import (
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    DOMAIN,
    SERVICE_SET_PRESET_MODE,
    FanEntity,
    FanEntityFeature,
    NotValidPresetModeError,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from .common import MockFan

from tests.common import setup_test_component_platform
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor for tryke fixture resolution."""
    return 0


class BaseFan(FanEntity):
    """Implementation of the abstract FanEntity."""

    def __init__(self) -> None:
        """Initialize the fan."""


@test
async def fanentity(
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test fan entity methods."""
    fan = BaseFan()
    expect(fan.state).to_equal("off")
    expect(fan.preset_modes).to_be(None)
    expect(fan.supported_features).to_equal(0)
    expect(fan.percentage_step).to_equal(1)
    expect(fan.speed_count).to_equal(100)
    expect(fan.capability_attributes).to_equal({})
    # Test set_speed not required
    expect(lambda: fan.oscillate(True)).to_raise(NotImplementedError)
    expect(lambda: fan.set_speed("low")).to_raise(AttributeError)
    expect(lambda: fan.set_percentage(0)).to_raise(NotImplementedError)
    expect(lambda: fan.set_preset_mode("auto")).to_raise(NotImplementedError)
    expect(lambda: fan.turn_on()).to_raise(NotImplementedError)
    expect(lambda: fan.turn_off()).to_raise(NotImplementedError)


@test
async def async_fanentity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async fan entity methods."""
    fan = BaseFan()
    fan.hass = hass
    expect(fan.state).to_equal("off")
    expect(fan.preset_modes).to_be(None)
    expect(fan.supported_features).to_equal(0)
    expect(fan.percentage_step).to_equal(1)
    expect(fan.speed_count).to_equal(100)
    expect(fan.capability_attributes).to_equal({})
    # Test set_speed not required
    async with expect_raises_async(NotImplementedError):
        await fan.async_oscillate(True)
    async with expect_raises_async(AttributeError):
        await fan.async_set_speed("low")
    async with expect_raises_async(NotImplementedError):
        await fan.async_set_percentage(0)
    async with expect_raises_async(NotImplementedError):
        await fan.async_set_preset_mode("auto")
    async with expect_raises_async(NotImplementedError):
        await fan.async_turn_on()
    async with expect_raises_async(NotImplementedError):
        await fan.async_turn_off()
    async with expect_raises_async(NotImplementedError):
        await fan.async_increase_speed()
    async with expect_raises_async(NotImplementedError):
        await fan.async_decrease_speed()


@test.cases(
    test.case(
        "current_direction",
        attribute_name="current_direction",
        attribute_value="forward",
    ),
    test.case("oscillating", attribute_name="oscillating", attribute_value=True),
    test.case("percentage", attribute_name="percentage", attribute_value=50),
    test.case("preset_mode", attribute_name="preset_mode", attribute_value="medium"),
    test.case(
        "preset_modes",
        attribute_name="preset_modes",
        attribute_value=["low", "medium", "high"],
    ),
    test.case("speed_count", attribute_name="speed_count", attribute_value=50),
    test.case(
        "supported_features", attribute_name="supported_features", attribute_value=1
    ),
)
async def fanentity_attributes(
    attribute_name: str,
    attribute_value: object,
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test fan entity attribute shorthand."""
    fan = BaseFan()
    setattr(fan, f"_attr_{attribute_name}", attribute_value)
    expect(getattr(fan, attribute_name)).to_equal(attribute_value)


@test
async def preset_mode_validation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test preset mode validation."""
    await hass.async_block_till_done()

    test_fan = MockFan(
        name="Support fan with preset_mode support",
        supported_features=FanEntityFeature.PRESET_MODE,
        unique_id="unique_support_preset_mode",
        preset_modes=["auto", "eco"],
    )
    setup_test_component_platform(hass, "fan", [test_fan])

    expect(
        await async_setup_component(hass, "fan", {"fan": {"platform": "test"}})
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("fan.support_fan_with_preset_mode_support")
    expect(state.attributes.get(ATTR_PRESET_MODES)).to_equal(["auto", "eco"])

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": "fan.support_fan_with_preset_mode_support",
            "preset_mode": "eco",
        },
        blocking=True,
    )

    state = hass.states.get("fan.support_fan_with_preset_mode_support")
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal("eco")

    raised: NotValidPresetModeError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                "entity_id": "fan.support_fan_with_preset_mode_support",
                "preset_mode": "invalid",
            },
            blocking=True,
        )
    except NotValidPresetModeError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_preset_mode")

    raised = None
    try:
        await test_fan._valid_preset_mode_or_raise("invalid")
    except NotValidPresetModeError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_preset_mode")
