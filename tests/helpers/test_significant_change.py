"""Test significant change helper."""

from types import MappingProxyType
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import significant_change

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@fixture
async def checker(
    hass: HomeAssistant = Depends(hass),
) -> significant_change.SignificantlyChangedChecker:
    """Checker fixture."""
    checker = await significant_change.create_checker(hass, "test")

    def async_check_significant_change(
        _hass, old_state, _old_attrs, new_state, _new_attrs, **kwargs
    ):
        return abs(float(old_state) - float(new_state)) > 4

    hass.data[significant_change.DATA_FUNCTIONS]["test_domain"] = (
        async_check_significant_change
    )
    return checker


@test
async def signicant_change(
    checker: significant_change.SignificantlyChangedChecker = Depends(checker),
) -> None:
    """Test initialize helper works."""
    ent_id = "test_domain.test_entity"
    attrs = {ATTR_DEVICE_CLASS: SensorDeviceClass.BATTERY}

    expect(checker.async_is_significant_change(State(ent_id, "100", attrs))).to_be(True)

    # Same state is not significant.
    expect(checker.async_is_significant_change(State(ent_id, "100", attrs))).to_be(
        False
    )

    # State under 5 difference is not significant. (per test mock)
    expect(checker.async_is_significant_change(State(ent_id, "96", attrs))).to_be(False)

    # Make sure we always compare against last significant change
    expect(checker.async_is_significant_change(State(ent_id, "95", attrs))).to_be(True)

    # State turned unknown
    expect(
        checker.async_is_significant_change(State(ent_id, STATE_UNKNOWN, attrs))
    ).to_be(True)

    # State turned unavailable
    expect(checker.async_is_significant_change(State(ent_id, "100", attrs))).to_be(True)
    expect(
        checker.async_is_significant_change(State(ent_id, STATE_UNAVAILABLE, attrs))
    ).to_be(True)


@test
async def significant_change_extra(
    checker: significant_change.SignificantlyChangedChecker = Depends(checker),
) -> None:
    """Test extra significant checker works."""
    ent_id = "test_domain.test_entity"
    attrs = {ATTR_DEVICE_CLASS: SensorDeviceClass.BATTERY}

    expect(
        checker.async_is_significant_change(State(ent_id, "100", attrs), extra_arg=1)
    ).to_be(True)
    expect(
        checker.async_is_significant_change(State(ent_id, "200", attrs), extra_arg=1)
    ).to_be(True)

    # Reset the last significiant change to 100 to repeat test but with
    # extra checker installed.
    expect(
        checker.async_is_significant_change(State(ent_id, "100", attrs), extra_arg=1)
    ).to_be(True)

    def extra_significant_check(
        hass: HomeAssistant,
        old_state: str,
        old_attrs: dict | MappingProxyType,
        old_extra_arg: Any,
        new_state: str,
        new_attrs: dict | MappingProxyType,
        new_extra_arg: Any,
    ) -> bool | None:
        return old_extra_arg != new_extra_arg

    checker.extra_significant_check = extra_significant_check

    # This is normally a significant change (100 -> 200), but the extra arg check marks it
    # as insignificant.
    expect(
        checker.async_is_significant_change(State(ent_id, "200", attrs), extra_arg=1)
    ).to_be(False)
    expect(
        checker.async_is_significant_change(State(ent_id, "200", attrs), extra_arg=2)
    ).to_be(True)


@test
async def check_valid_float() -> None:
    """Test extra significant checker works."""
    expect(significant_change.check_valid_float("1")).to_be(True)
    expect(significant_change.check_valid_float("1.0")).to_be(True)
    expect(significant_change.check_valid_float(1)).to_be(True)
    expect(significant_change.check_valid_float(1.0)).to_be(True)
    expect(significant_change.check_valid_float("")).to_be(False)
    expect(significant_change.check_valid_float("invalid")).to_be(False)
    expect(significant_change.check_valid_float("1.1.1")).to_be(False)
