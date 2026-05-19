"""The tests for the Select component (tryke port)."""

from unittest.mock import MagicMock

import pytest
from tryke import Depends, fixture, test

from homeassistant.components.select import (
    ATTR_CYCLE,
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN,
    SERVICE_SELECT_FIRST,
    SERVICE_SELECT_LAST,
    SERVICE_SELECT_NEXT,
    SERVICE_SELECT_OPTION,
    SERVICE_SELECT_PREVIOUS,
    SelectEntity,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_PLATFORM, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from .common import MockSelectEntity

from tests.common import setup_test_component_platform
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_select_entities() -> list[MockSelectEntity]:
    """Return a list of mock select entities."""
    return [
        MockSelectEntity(
            name="select 1",
            unique_id="unique_select_1",
            options=["option 1", "option 2", "option 3"],
            current_option="option 1",
        ),
        MockSelectEntity(
            name="select 2",
            unique_id="unique_select_2",
            options=["option 1", "option 2", "option 3"],
            current_option=None,
        ),
    ]


class _LocalMockSelectEntity(SelectEntity):
    """Mock SelectEntity to use in tests."""

    _attr_current_option = "option_one"
    _attr_options = ["option_one", "option_two", "option_three"]


@test
async def select(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test getting data from the mocked select entity."""
    select = _LocalMockSelectEntity()
    assert select.current_option == "option_one"
    assert select.state == "option_one"
    assert select.options == ["option_one", "option_two", "option_three"]

    # Test none selected
    select._attr_current_option = None
    assert select.current_option is None
    assert select.state is None

    # Test none existing selected
    select._attr_current_option = "option_four"
    assert select.current_option == "option_four"
    assert select.state is None

    select.hass = hass

    with pytest.raises(NotImplementedError):
        await select.async_first()

    with pytest.raises(NotImplementedError):
        await select.async_last()

    with pytest.raises(NotImplementedError):
        await select.async_next(cycle=False)

    with pytest.raises(NotImplementedError):
        await select.async_previous(cycle=False)

    with pytest.raises(NotImplementedError):
        await select.async_select_option("option_one")

    select.select_option = MagicMock()
    select._attr_current_option = None

    await select.async_first()
    assert select.select_option.call_args[0][0] == "option_one"

    await select.async_last()
    assert select.select_option.call_args[0][0] == "option_three"

    await select.async_next(cycle=False)
    assert select.select_option.call_args[0][0] == "option_one"

    await select.async_previous(cycle=False)
    assert select.select_option.call_args[0][0] == "option_three"

    await select.async_select_option("option_two")
    assert select.select_option.call_args[0][0] == "option_two"

    assert select.select_option.call_count == 5

    assert select.capability_attributes[ATTR_OPTIONS] == [
        "option_one",
        "option_two",
        "option_three",
    ]


@test
async def custom_integration_and_validation(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_select_entities: list[MockSelectEntity] = Depends(mock_select_entities),
) -> None:
    """Test we can only select valid options."""
    setup_test_component_platform(hass, DOMAIN, mock_select_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    assert hass.states.get("select.select_1").state == "option 1"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_OPTION: "option 2", ATTR_ENTITY_ID: "select.select_1"},
        blocking=True,
    )

    hass.states.async_set("select.select_1", "option 2")
    await hass.async_block_till_done()
    assert hass.states.get("select.select_1").state == "option 2"

    # test ServiceValidationError trigger
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_OPTION: "option invalid", ATTR_ENTITY_ID: "select.select_1"},
            blocking=True,
        )
    await hass.async_block_till_done()
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "not_valid_option"

    assert hass.states.get("select.select_1").state == "option 2"

    assert hass.states.get("select.select_2").state == STATE_UNKNOWN

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_OPTION: "option invalid", ATTR_ENTITY_ID: "select.select_2"},
            blocking=True,
        )
    await hass.async_block_till_done()
    assert hass.states.get("select.select_2").state == STATE_UNKNOWN

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_OPTION: "option 3", ATTR_ENTITY_ID: "select.select_2"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("select.select_2").state == "option 3"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_FIRST,
        {ATTR_ENTITY_ID: "select.select_2"},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 1"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_LAST,
        {ATTR_ENTITY_ID: "select.select_2"},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 3"

    # Do no cycle
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_NEXT,
        {ATTR_ENTITY_ID: "select.select_2", ATTR_CYCLE: False},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 3"

    # Do cycle (default behavior)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_NEXT,
        {ATTR_ENTITY_ID: "select.select_2"},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 1"

    # Do not cycle
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_PREVIOUS,
        {ATTR_ENTITY_ID: "select.select_2", ATTR_CYCLE: False},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 1"

    # Do cycle (default behavior)
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_PREVIOUS,
        {ATTR_ENTITY_ID: "select.select_2"},
        blocking=True,
    )
    assert hass.states.get("select.select_2").state == "option 3"
