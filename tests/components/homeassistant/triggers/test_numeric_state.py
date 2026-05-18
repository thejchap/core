"""The tests for numeric state automation."""

from datetime import timedelta
import logging
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components import automation
from homeassistant.components.homeassistant.triggers import (
    numeric_state as numeric_state_trigger,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    STATE_UNAVAILABLE,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import service_calls, setup_comp

from tests.common import assert_setup_component, async_fire_time_changed
from tests.hass_tryke_helpers import expect_raises_async
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def setup_comp_numeric(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_comp),
) -> None:
    """Initialize input_number and base states."""
    await async_setup_component(
        hass,
        "input_number",
        {
            "input_number": {
                "value_3": {"min": 0, "max": 255, "initial": 3},
                "value_5": {"min": 0, "max": 255, "initial": 5},
                "value_8": {"min": 0, "max": 255, "initial": 8},
                "value_10": {"min": 0, "max": 255, "initial": 10},
                "value_12": {"min": 0, "max": 255, "initial": 12},
                "value_100": {"min": 0, "max": 255, "initial": 100},
            }
        },
    )
    hass.states.async_set("number.value_10", 10)
    hass.states.async_set("sensor.value_10", 10)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp_numeric),
) -> int:
    """Anchor fixture - autouse setup_comp and mock_network for every test."""
    return 0


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_not_fires_on_entity_removal(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with removed entity."""
    hass.states.async_set("test.entity", 11)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_remove("test.entity")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_fires_on_entity_change_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    context = Context()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)
    # 9 is below 10
    hass.states.async_set("test.entity", 9, context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)

    hass.states.async_set("test.entity", 12)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[0].data["id"]).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_fires_on_entity_change_below_uuid(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity specified by registry entry id."""
    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="entity"
    )
    expect(entry.entity_id).to_equal("test.entity")

    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    context = Context()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": entry.id,
                        "below": below,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)
    # 9 is below 10
    hass.states.async_set("test.entity", 9, context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)

    hass.states.async_set("test.entity", 12)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[0].data["id"]).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_fires_on_entity_change_over_to_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_fires_on_entities_change_over_to_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entities."""
    hass.states.async_set("test.entity_1", 11)
    hass.states.async_set("test.entity_2", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_not_fires_on_entity_change_below_to_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    context = Context()
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9, context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)

    hass.states.async_set("test.entity", 5)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", 3)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_not_below_fires_on_entity_change_to_equal(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 10)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
    test.case("number", below="number.value_10"),
    test.case("sensor", below="sensor.value_10"),
)
async def if_not_fires_on_initial_entity_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing when starting with a match."""
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 8)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
    test.case("number", above="number.value_10"),
    test.case("sensor", above="sensor.value_10"),
)
async def if_not_fires_on_initial_entity_above(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing when starting with a match."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 12)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
    test.case("number", above="number.value_10"),
    test.case("sensor", above="sensor.value_10"),
)
async def if_fires_on_entity_change_above(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_unavailable_at_startup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity at startup."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": 10,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
)
async def if_fires_on_entity_change_below_to_above(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
)
async def if_not_fires_on_entity_change_above_to_above(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 12)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", 15)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
)
async def if_not_above_fires_on_entity_change_to_equal(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 10)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("ints", above=5, below=10),
    test.case("int_input", above=5, below="input_number.value_10"),
    test.case("input_int", above="input_number.value_5", below=10),
    test.case("inputs", above="input_number.value_5", below="input_number.value_10"),
)
async def if_fires_on_entity_change_below_range(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("ints", above=5, below=10),
    test.case("int_input", above=5, below="input_number.value_10"),
    test.case("input_int", above="input_number.value_5", below=10),
    test.case("inputs", above="input_number.value_5", below="input_number.value_10"),
)
async def if_fires_on_entity_change_below_above_range(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 4)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("ints", above=5, below=10),
    test.case("int_input", above=5, below="input_number.value_10"),
    test.case("input_int", above="input_number.value_5", below=10),
    test.case("inputs", above="input_number.value_5", below="input_number.value_10"),
)
async def if_fires_on_entity_change_over_to_below_range(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                        "above": above,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("ints", above=5, below=10),
    test.case("int_input", above=5, below="input_number.value_10"),
    test.case("input_int", above="input_number.value_5", below=10),
    test.case("inputs", above="input_number.value_5", below="input_number.value_10"),
)
async def if_fires_on_entity_change_over_to_below_above_range(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing with changed entity."""
    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": above,
                        "above": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 4)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=100),
    test.case("input_number", below="input_number.value_100"),
)
async def if_not_fires_if_entity_not_match(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if not fired with non matching entity."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.another_entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_not_fires_and_warns_if_below_entity_unknown(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if warns with unknown below entity."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": "input_number.unknown",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    caplog.clear()
    caplog.set_level(logging.WARNING)

    hass.states.async_set("test.entity", 1)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    expect(len(caplog.records)).to_equal(1)
    expect(caplog.records[0].levelno).to_equal(logging.WARNING)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_fires_on_entity_change_below_with_attribute(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    hass.states.async_set("test.entity", 11, {"test_attribute": 11})
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 9, {"test_attribute": 11})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_not_fires_on_entity_change_not_below_with_attribute(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", 11, {"test_attribute": 9})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_fires_on_attribute_change_with_attribute_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    hass.states.async_set("test.entity", "entity", {"test_attribute": 11})
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", "entity", {"test_attribute": 9})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_not_fires_on_attribute_change_with_attribute_not_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", "entity", {"test_attribute": 11})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_not_fires_on_entity_change_with_attribute_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    # 11 is not below 10, entity state value should not be tested
    hass.states.async_set("test.entity", "9", {"test_attribute": 11})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def if_not_fires_on_entity_change_with_not_attribute_below(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", "entity")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def fires_on_attr_change_with_attribute_below_and_multiple_attr(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test attributes change."""
    hass.states.async_set(
        "test.entity", "entity", {"test_attribute": 11, "not_test_attribute": 11}
    )
    await hass.async_block_till_done()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set(
        "test.entity", "entity", {"test_attribute": 9, "not_test_attribute": 11}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", below=10),
    test.case("input_number", below="input_number.value_10"),
)
async def template_list(
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test template list."""
    hass.states.async_set("test.entity", "entity", {"test_attribute": [11, 15, 11]})
    await hass.async_block_till_done()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute[2] }}",
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", "entity", {"test_attribute": [11, 15, 3]})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("float", below=10.0),
    test.case("input_number", below="input_number.value_10"),
)
async def template_string(
    below: float | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test template string."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": (
                            "{{ state.attributes.test_attribute | multiply(10) }}"
                        ),
                        "below": below,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.below }}"
                                " - {{ trigger.above }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)
    hass.states.async_set("test.entity", "test state 1", {"test_attribute": "1.2"})
    await hass.async_block_till_done()
    hass.states.async_set("test.entity", "test state 2", {"test_attribute": "0.9"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"numeric_state - test.entity - {below} - None - test state 1 - test state 2"
    )


@test
async def not_fires_on_attr_change_with_attr_not_below_multiple_attr(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if not fired changed attributes."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": "{{ state.attributes.test_attribute }}",
                        "below": 10,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.states.async_set(
        "test.entity", "entity", {"test_attribute": 11, "not_test_attribute": 9}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_action(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test if action."""
    entity_id = "domain.test_entity"
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "numeric_state",
                        "entity_id": entity_id,
                        "above": above,
                        "below": below,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(entity_id, 10)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entity_id, 8)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entity_id, 9)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fails_setup_bad_for(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure for bad for."""
    hass.states.async_set("test.entity", 5)
    await hass.async_block_till_done()

    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "numeric_state",
                            "entity_id": "test.entity",
                            "above": above,
                            "below": below,
                            "for": {"invalid": 5},
                        },
                        "action": {"service": "homeassistant.turn_on"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(
        STATE_UNAVAILABLE
    )


@test
async def if_fails_setup_for_without_above_below(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failures for missing above or below."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "numeric_state",
                            "entity_id": "test.entity",
                            "for": {"seconds": 5},
                        },
                        "action": {"service": "homeassistant.turn_on"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(
        STATE_UNAVAILABLE
    )


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_not_fires_on_entity_change_with_for(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on entity change with for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    hass.states.async_set("test.entity", 15)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_not_fires_on_entities_change_with_for_after_stop(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on entities change with for after stop."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": [
                        {"delay": "0.0001"},
                        {"service": "test.automation"},
                    ],
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity_1", 9)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity_1", 15)
    hass.states.async_set("test.entity_2", 15)
    await hass.async_block_till_done()
    hass.states.async_set("test.entity_1", 9)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_entity_change_with_for_attribute_change(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for and attribute change."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=4))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity", 9, attributes={"mock_attr": "attr_change"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=4))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_entity_change_with_for(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", above=10),
    test.case("input_number", above="input_number.value_10"),
)
async def wait_template_with_trigger(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test using wait template with 'trigger.entity_id'."""
    hass.states.async_set("test.entity", "0")
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                    },
                    "action": [
                        {"wait_template": "{{ states(trigger.entity_id) | int < 10 }}"},
                        {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.to_state.state }}"
                                )
                            },
                        },
                    ],
                }
            },
        )
    ).to_be(True)

    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "12")
    hass.states.async_set("test.entity", "8")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("numeric_state - test.entity - 12")


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_entities_change_no_overlap(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with no overlap."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "{{ trigger.entity_id }}"},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test.entity_1")

    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("test.entity_2")


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_entities_change_overlap(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with overlap."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "above": above,
                        "below": below,
                        "for": {"seconds": 5},
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": "{{ trigger.entity_id }}"},
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 15)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test.entity_1")

    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("test.entity_2")


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_change_with_for_template_1(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": {"seconds": "{{ 5 }}"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_change_with_for_template_2(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": "{{ 5 }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_change_with_for_template_3(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": "00:00:{{ 5 }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_not_fires_on_error_with_for_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on error with for template."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": 100,
                        "for": "00:00:05",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", 101)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=3))
    hass.states.async_set("test.entity", "unavailable")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=3))
    hass.states.async_set("test.entity", 101)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def invalid_for_template(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for invalid for template."""
    hass.states.async_set("test.entity", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "below": below,
                        "for": "{{ five }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    with patch.object(numeric_state_trigger, "_LOGGER") as mock_logger:
        hass.states.async_set("test.entity", 9)
        await hass.async_block_till_done()
        expect(mock_logger.error.called).to_be(True)


@test.cases(
    test.case("ints", above=8, below=12),
    test.case("int_input", above=8, below="input_number.value_12"),
    test.case("input_int", above="input_number.value_8", below=12),
    test.case("inputs", above="input_number.value_8", below="input_number.value_12"),
)
async def if_fires_on_entities_change_overlap_for_template(
    above: int | str,
    below: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with overlap and for template."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "above": above,
                        "below": below,
                        "for": (
                            '{{ 5 if trigger.entity_id == "test.entity_1" else 10 }}'
                        ),
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.entity_id }} - {{ trigger.for }}"
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 15)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test.entity_1 - 0:00:05")

    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("test.entity_2 - 0:00:10")


@test
async def below_above(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test above cannot be above below."""
    async with expect_raises_async(vol.Invalid):
        await numeric_state_trigger.async_validate_trigger_config(
            hass, {"platform": "numeric_state", "above": 1200, "below": 1000}
        )


@test
async def schema_unacceptable_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test input_number, number & sensor only is accepted for above/below."""
    async with expect_raises_async(vol.Invalid):
        await numeric_state_trigger.async_validate_trigger_config(
            hass,
            {
                "platform": "numeric_state",
                "above": "input_datetime.some_input",
                "below": 1000,
            },
        )
    async with expect_raises_async(vol.Invalid):
        await numeric_state_trigger.async_validate_trigger_config(
            hass,
            {
                "platform": "numeric_state",
                "below": "input_datetime.some_input",
                "above": 1200,
            },
        )


@test.cases(
    test.case("int", above=3),
    test.case("input_number", above="input_number.value_3"),
)
async def attribute_if_fires_on_entity_change_with_both_filters(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if both filters are match attribute."""
    hass.states.async_set("test.entity", "bla", {"test-measurement": 1})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "attribute": "test-measurement",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "bla", {"test-measurement": 4})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("int", above=3),
    test.case("input_number", above="input_number.value_3"),
)
async def attribute_if_not_fires_on_entities_change_with_for_after_stop(
    above: int | str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on entity change with for after stop trigger."""
    hass.states.async_set("test.entity", "bla", {"test-measurement": 1})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "above": above,
                        "attribute": "test-measurement",
                        "for": 5,
                    },
                    "action": [
                        {"delay": "0.0001"},
                        {"service": "test.automation"},
                    ],
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "bla", {"test-measurement": 4})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(test.case("default", above=8, below=12))
async def variables_priority(
    above: int,
    below: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test an externally defined trigger variable is overridden."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"trigger": "illegal"},
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "above": above,
                        "below": below,
                        "for": (
                            '{{ 5 if trigger.entity_id == "test.entity_1" else 10 }}'
                        ),
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.entity_id }} - {{ trigger.for }}"
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 15)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test.entity_1 - 0:00:05")


@test.cases(
    test.case("mult_1_fires", multiplier=1, expected_calls=1),
    test.case("mult_5_skips", multiplier=5, expected_calls=0),
)
async def template_variable(
    multiplier: int,
    expected_calls: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test template variable."""
    hass.states.async_set("test.entity", "entity", {"test_attribute": [11, 15, 11]})
    await hass.async_block_till_done()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"multiplier": multiplier},
                    "trigger": {
                        "platform": "numeric_state",
                        "entity_id": "test.entity",
                        "value_template": (
                            "{{ state.attributes.test_attribute[2] * multiplier}}"
                        ),
                        "below": 10,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    # 3 is below 10
    hass.states.async_set("test.entity", "entity", {"test_attribute": [11, 15, 3]})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(expected_calls)
