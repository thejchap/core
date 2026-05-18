"""The test for state automation."""

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.homeassistant.triggers import state as state_trigger
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
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _state_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_comp),
) -> None:
    """Initialize components and set initial test.entity state."""
    hass.states.async_set("test.entity", "hello")


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(_state_setup),
) -> int:
    """Anchor fixture - autouse setup_comp and mock_network for every test."""
    return 0


@test
async def if_fires_on_entity_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change."""
    context = Context()
    hass.states.async_set("test.entity", "hello")
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "state", "entity_id": "test.entity"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                                " - {{ trigger.id }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)
    expect(service_calls[0].data["some"]).to_equal(
        "state - test.entity - hello - world - None - 0"
    )

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)
    hass.states.async_set("test.entity", "planet")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_entity_change_uuid(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change."""
    context = Context()

    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="beer"
    )

    expect(entry.entity_id).to_equal("test.beer")

    hass.states.async_set("test.beer", "hello")
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "state", "entity_id": entry.id},
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.for }}"
                                " - {{ trigger.id }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.beer", "world", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)
    expect(service_calls[0].data["some"]).to_equal(
        "state - test.beer - hello - world - None - 0"
    )

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)
    hass.states.async_set("test.beer", "planet")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_entity_change_with_from_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_not_from_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change inverse filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "not_from": "hello",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(bool(service_calls)).to_be(False)

    hass.states.async_set("test.entity", "universum")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_to_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with to filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_not_to_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with to filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "not_to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(bool(service_calls)).to_be(False)

    hass.states.async_set("test.entity", "universum")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_from_filter_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": None,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    hass.states.async_set("test.entity", "world", {"attribute": 5})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_to_filter_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with to filter."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": None,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    hass.states.async_set("test.entity", "world", {"attribute": 5})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_attribute_change_with_to_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on attribute change."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world", {"test_attribute": 11})
    hass.states.async_set("test.entity", "world", {"test_attribute": 12})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_both_filters(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if both filters are a non match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                        "to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_not_from_to(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if not from doesn't match and to match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "not_from": ["hello", "galaxy"],
                        "to": ["galaxy", "universe"],
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(bool(service_calls)).to_be(False)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(bool(service_calls)).to_be(False)

    hass.states.async_set("test.entity", "galaxy")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "milky_way")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "universe")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_entity_change_with_from_not_to(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if not from doesn't match and to match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": ["hello", "galaxy"],
                        "not_to": ["galaxy", "universe"],
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "hello")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "galaxy")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "milky_way")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)

    hass.states.async_set("test.entity", "universe")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_not_fires_if_to_filter_not_match(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing if to filter is not a match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                        "to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "moon")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_not_fires_if_from_filter_not_match(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing if from filter is not a match."""
    hass.states.async_set("test.entity", "bye")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                        "to": "world",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_not_fires_if_entity_not_match(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing if entity is not matching."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.another_entity",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_action(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for to action."""
    entity_id = "domain.test_entity"
    test_state = "new_state"
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": [
                        {
                            "condition": "state",
                            "entity_id": entity_id,
                            "state": test_state,
                        }
                    ],
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(entity_id, test_state)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entity_id, test_state + "something")
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_fails_setup_if_to_boolean_value(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure for boolean to."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "state",
                            "entity_id": "test.entity",
                            "to": True,
                        },
                        "action": {"service": "homeassistant.turn_on"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)


@test
async def if_fails_setup_if_from_boolean_value(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure for boolean from."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "state",
                            "entity_id": "test.entity",
                            "from": True,
                        },
                        "action": {"service": "homeassistant.turn_on"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)


@test
async def if_fails_setup_bad_for(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure for bad for."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {
                            "platform": "state",
                            "entity_id": "test.entity",
                            "to": "world",
                            "for": {"invalid": 5},
                        },
                        "action": {"service": "homeassistant.turn_on"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)


@test
async def if_not_fires_on_entity_change_with_for(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    hass.states.async_set("test.entity", "not_world")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_not_fires_on_entities_change_with_for_after_stop(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on entity change with for after stop trigger."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "to": "world",
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
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", "world")
    hass.states.async_set("test.entity_2", "world")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity_1", "world_no")
    hass.states.async_set("test.entity_2", "world_no")
    await hass.async_block_till_done()
    hass.states.async_set("test.entity_1", "world")
    hass.states.async_set("test.entity_2", "world")
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


@test
async def if_fires_on_entity_change_with_for_attribute_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for and attribute change."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=4))
    async_fire_time_changed(hass)
    hass.states.async_set(
        "test.entity", "world", attributes={"mock_attr": "attr_change"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=4))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_for_multiple_force_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for and force update."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.force_entity",
                        "to": "world",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.force_entity", "world", None, True)
    await hass.async_block_till_done()
    for _ in range(4):
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        hass.states.async_set("test.force_entity", "world", None, True)
        await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    freezer.tick(timedelta(seconds=4))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_for(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_entity_change_with_for_without_to(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "hello")
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=4))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_does_not_fires_on_entity_change_with_for_without_to_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity change with for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "for": {"seconds": 5},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for i in range(10):
        hass.states.async_set("test.entity", str(i))
        await hass.async_block_till_done()
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(0)


@test
async def if_fires_on_entity_creation_and_removal(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entity creation and removal, with to/from constraints."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {
                            "platform": "state",
                            "entity_id": "test.entity_0",
                        },
                        "action": {"service": "test.automation"},
                    },
                    {
                        "trigger": {
                            "platform": "state",
                            "from": "hello",
                            "entity_id": "test.entity_1",
                        },
                        "action": {"service": "test.automation"},
                    },
                    {
                        "trigger": {
                            "platform": "state",
                            "to": "world",
                            "entity_id": "test.entity_2",
                        },
                        "action": {"service": "test.automation"},
                    },
                ],
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    context_0 = Context()
    context_1 = Context()
    context_2 = Context()

    hass.states.async_set("test.entity_0", "any", context=context_0)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context_0.id)

    hass.states.async_set("test.entity_1", "hello", context=context_1)
    hass.states.async_set("test.entity_2", "world", context=context_2)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].context.parent_id).to_equal(context_2.id)

    expect(hass.states.async_remove("test.entity_1", context=context_1)).to_be(True)
    expect(hass.states.async_remove("test.entity_2", context=context_2)).to_be(True)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].context.parent_id).to_equal(context_1.id)

    expect(hass.states.async_remove("test.entity_0", context=context_0)).to_be(True)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].context.parent_id).to_equal(context_0.id)


@test
async def if_fires_on_for_condition(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if condition is on."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=10)
    with patch("homeassistant.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = point1
        hass.states.async_set("test.entity", "on")
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "condition": {
                            "condition": "state",
                            "entity_id": "test.entity",
                            "state": "on",
                            "for": {"seconds": 5},
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        mock_utcnow.return_value = point2
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_for_condition_attribute_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if condition is on with attribute change."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=4)
    point3 = point1 + timedelta(seconds=8)
    with patch("homeassistant.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = point1
        hass.states.async_set("test.entity", "on")
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "condition": {
                            "condition": "state",
                            "entity_id": "test.entity",
                            "state": "on",
                            "for": {"seconds": 5},
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        mock_utcnow.return_value = point2
        hass.states.async_set(
            "test.entity", "on", attributes={"mock_attr": "attr_change"}
        )
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        mock_utcnow.return_value = point3
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)


@test
async def if_fails_setup_for_without_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if no time is provided."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "bla"},
                        "condition": {
                            "condition": "state",
                            "entity_id": "test.entity",
                            "state": "on",
                            "for": {},
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)


@test
async def if_fails_setup_for_without_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if no entity is provided."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "bla"},
                        "condition": {
                            "condition": "state",
                            "state": "on",
                            "for": {"seconds": 5},
                        },
                        "action": {"service": "test.automation"},
                    }
                },
            )
        ).to_be(True)
    expect(hass.states.get("automation.automation_0").state).to_equal(STATE_UNAVAILABLE)


@test
async def wait_template_with_trigger(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test using wait template with 'trigger.entity_id'."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                    },
                    "action": [
                        {"wait_template": "{{ is_state(trigger.entity_id, 'hello') }}"},
                        {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
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

    hass.states.async_set("test.entity", "world")
    hass.states.async_set("test.entity", "hello")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        "state - test.entity - hello - world"
    )


@test
async def if_fires_on_entities_change_no_overlap(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with no overlap."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "to": "world",
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

    hass.states.async_set("test.entity_1", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("test.entity_1")

    hass.states.async_set("test.entity_2", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("test.entity_2")


@test
async def if_fires_on_entities_change_overlap(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with overlap."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "to": "world",
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

    hass.states.async_set("test.entity_1", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "hello")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
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


@test
async def if_fires_on_change_with_for_template_1(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": "{{ 5 }}"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_change_with_for_template_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": "{{ 5 }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_change_with_for_template_3(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": "00:00:{{ 5 }}",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_change_with_for_template_4(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"seconds": 5},
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": "{{ seconds }}"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("test.entity", "world")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_change_from_with_for(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with from/for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "media_player.foo",
                        "from": "playing",
                        "for": "00:00:30",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("media_player.foo", "playing")
    await hass.async_block_till_done()
    hass.states.async_set("media_player.foo", "paused")
    await hass.async_block_till_done()
    hass.states.async_set("media_player.foo", "stopped")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=1))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_not_fires_on_change_from_with_for(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on change with from/for."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "media_player.foo",
                        "from": "playing",
                        "for": "00:00:30",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set("media_player.foo", "playing")
    await hass.async_block_till_done()
    hass.states.async_set("media_player.foo", "paused")
    await hass.async_block_till_done()
    hass.states.async_set("media_player.foo", "playing")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=1))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def invalid_for_template_1(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for invalid for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "to": "world",
                        "for": {"seconds": "{{ five }}"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    with patch.object(state_trigger, "_LOGGER") as mock_logger:
        hass.states.async_set("test.entity", "world")
        await hass.async_block_till_done()
        expect(mock_logger.error.called).to_be(True)


@test
async def if_fires_on_entities_change_overlap_for_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on entities change with overlap and for template."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "to": "world",
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

    hass.states.async_set("test.entity_1", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "hello")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
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
async def attribute_if_fires_on_entity_change_with_both_filters(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if both filters are match attribute."""
    hass.states.async_set("test.entity", "bla", {"name": "hello"})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                        "to": "world",
                        "attribute": "name",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "bla", {"name": "world"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def attribute_if_fires_on_entity_where_attr_stays_constant(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if attribute stays the same."""
    hass.states.async_set(
        "test.entity", "bla", {"name": "hello", "other": "old_value"}
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "attribute": "name",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "test.entity", "bla", {"name": "hello", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(
        "test.entity", "bla", {"name": "hello", "other": "new_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(
        "test.entity", "bla", {"name": "world", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def attribute_if_fires_on_entity_where_attr_stays_constant_filter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if attribute stays the same."""
    hass.states.async_set("test.entity", "bla", {"name": "other_name"})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "attribute": "name",
                        "to": "best_name",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "test.entity", "bla", {"name": "best_name", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(
        "test.entity", "bla", {"name": "best_name", "other": "new_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(
        "test.entity", "bla", {"name": "other_name", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def attribute_if_fires_on_entity_where_attr_stays_constant_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if attribute stays the same."""
    hass.states.async_set(
        "test.entity", "bla", {"name": "hello", "other": "old_value"}
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "attribute": "name",
                        "to": None,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "test.entity", "bla", {"name": "name_1", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(
        "test.entity", "bla", {"name": "name_1", "other": "new_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(
        "test.entity", "bla", {"name": "name_2", "other": "old_value"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def attribute_if_not_fires_on_entities_change_with_for_after_stop(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on entity change with for after stop trigger."""
    hass.states.async_set("test.entity", "bla", {"name": "hello"})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": "hello",
                        "to": "world",
                        "attribute": "name",
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

    hass.states.async_set("test.entity", "bla", {"name": "world"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    hass.states.async_set(
        "test.entity", "bla", {"name": "world", "something": "else"}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set("test.entity", "bla", {"name": "hello"})
    hass.states.async_set("test.entity", "bla", {"name": "world"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_remove("test.entity")
    await hass.async_block_till_done()

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def attribute_if_fires_on_entity_change_with_both_filters_boolean(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if both filters are match attribute."""
    hass.states.async_set("test.entity", "bla", {"happening": False})

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "state",
                        "entity_id": "test.entity",
                        "from": False,
                        "to": True,
                        "attribute": "happening",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("test.entity", "bla", {"happening": True})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def variables_priority(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test an externally defined trigger variable is overridden."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"trigger": "illegal"},
                    "trigger": {
                        "platform": "state",
                        "entity_id": ["test.entity_1", "test.entity_2"],
                        "to": "world",
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

    hass.states.async_set("test.entity_1", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "hello")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", "world")
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
