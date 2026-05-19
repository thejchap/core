"""The tests for the text component (tryke port)."""

from typing import Any

import pytest
from tryke import Depends, fixture, test

from homeassistant.components.text import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_PATTERN,
    ATTR_VALUE,
    DOMAIN,
    SERVICE_SET_VALUE,
    TextMode,
    _async_set_value,
)
from homeassistant.const import MAX_LENGTH_STATE_STATE
from homeassistant.core import HomeAssistant, ServiceCall, State
from homeassistant.helpers.restore_state import STORAGE_KEY as RESTORE_STATE_KEY
from homeassistant.setup import async_setup_component

from .common import MockRestoreText, MockTextEntity

from tests.common import (
    async_mock_restore_state_shutdown_restart,
    mock_restore_cache_with_extra_data,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@test
async def text_default(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test text entity with defaults."""
    text = MockTextEntity()
    text.hass = hass

    assert text.capability_attributes == {
        ATTR_MIN: 0,
        ATTR_MAX: MAX_LENGTH_STATE_STATE,
        ATTR_MODE: TextMode.TEXT,
        ATTR_PATTERN: None,
    }
    assert text.pattern is None
    assert text.state == "test"


@test
async def text_new_min_max_pattern(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test text entity with new min, max, and pattern."""
    text = MockTextEntity(native_min=-1, native_max=500, pattern=r"[a-z]")
    text.hass = hass

    assert text.capability_attributes == {
        ATTR_MIN: 0,
        ATTR_MAX: MAX_LENGTH_STATE_STATE,
        ATTR_MODE: TextMode.TEXT,
        ATTR_PATTERN: r"[a-z]",
    }


@test
async def text_set_value(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test text entity with set_value service."""
    text = MockTextEntity(native_min=1, native_max=5, pattern=r"[a-z]")
    text.hass = hass

    with pytest.raises(ValueError):
        await _async_set_value(
            text, ServiceCall(hass, DOMAIN, SERVICE_SET_VALUE, {ATTR_VALUE: ""})
        )

    with pytest.raises(ValueError):
        await _async_set_value(
            text,
            ServiceCall(hass, DOMAIN, SERVICE_SET_VALUE, {ATTR_VALUE: "hello world!"}),
        )

    with pytest.raises(ValueError):
        await _async_set_value(
            text, ServiceCall(hass, DOMAIN, SERVICE_SET_VALUE, {ATTR_VALUE: "HELLO"})
        )

    await _async_set_value(
        text, ServiceCall(hass, DOMAIN, SERVICE_SET_VALUE, {ATTR_VALUE: "test2"})
    )

    assert text.state == "test2"


@test
async def text_value_outside_bounds(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test text entity with value that is outside min and max."""
    with pytest.raises(ValueError):
        _ = MockTextEntity(
            "hello world", native_min=2, native_max=5, pattern=r"[a-z]"
        ).state
    with pytest.raises(ValueError):
        _ = MockTextEntity(
            "hello world", native_min=15, native_max=20, pattern=r"[a-z]"
        ).state


RESTORE_DATA = {
    "native_max": 5,
    "native_min": 1,
    # "mode": TextMode.TEXT,
    # "pattern": r"[A-Za-z0-9]",
    "native_value": "Hello",
}


@test
async def restore_number_save_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test RestoreNumber."""
    entity0 = MockRestoreText(
        name="Test",
        native_max=5,
        native_min=1,
        native_value="Hello",
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "text", {"text": {"platform": "test"}})
    await hass.async_block_till_done()

    # Trigger saving state
    await async_mock_restore_state_shutdown_restart(hass)

    assert len(hass_storage[RESTORE_STATE_KEY]["data"]) == 1
    state = hass_storage[RESTORE_STATE_KEY]["data"][0]["state"]
    assert state["entity_id"] == entity0.entity_id
    extra_data = hass_storage[RESTORE_STATE_KEY]["data"][0]["extra_data"]
    assert extra_data == RESTORE_DATA
    assert isinstance(extra_data["native_value"], str)


@test.cases(
    test.case(
        "hello",
        native_max=5,
        native_min=1,
        native_value="Hello",
        native_value_type=str,
        extra_data=RESTORE_DATA,
    ),
    test.case(
        "none_extra_data",
        native_max=255,
        native_min=1,
        native_value=None,
        native_value_type=type(None),
        extra_data=None,
    ),
    test.case(
        "empty_extra_data",
        native_max=255,
        native_min=1,
        native_value=None,
        native_value_type=type(None),
        extra_data={},
    ),
    test.case(
        "junk_extra_data",
        native_max=255,
        native_min=1,
        native_value=None,
        native_value_type=type(None),
        extra_data={"beer": 123},
    ),
    test.case(
        "bad_native_value",
        native_max=255,
        native_min=1,
        native_value=None,
        native_value_type=type(None),
        extra_data={"native_value": {}},
    ),
)
async def restore_number_restore_state(
    *,
    native_max: int,
    native_min: int,
    native_value: Any,
    native_value_type: type,
    extra_data: Any,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test RestoreNumber."""
    mock_restore_cache_with_extra_data(hass, ((State("text.test", ""), extra_data),))

    entity0 = MockRestoreText(
        native_max=native_max,
        native_min=native_min,
        name="Test",
        native_value=None,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "text", {"text": {"platform": "test"}})
    await hass.async_block_till_done()

    assert hass.states.get(entity0.entity_id)

    assert entity0.native_max == native_max
    assert entity0.native_min == native_min
    assert entity0.mode == TextMode.TEXT
    assert entity0.pattern is None
    assert entity0.native_value == native_value
    assert isinstance(entity0.native_value, native_value_type)
