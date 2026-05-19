"""The tests for the automation component."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.automation import (
    ATTR_SOURCE,
    EVENT_AUTOMATION_TRIGGERED,
    SERVICE_TRIGGER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import assert_setup_component, async_mock_service
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
def calls(hass: HomeAssistant = Depends(_trigger_executor)) -> list[ServiceCall]:
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "automation")


@test
async def service_data_not_a_dict(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test service data not dict."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "action": {"action": "test.automation", "data": 100},
                    }
                },
            )
        ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)
    expect("Result is not a Dictionary" in caplog.text).to_be(True)


@test
async def service_data_single_template(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test service data not dict."""
    with assert_setup_component(1, automation.DOMAIN):
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "action": {
                            "action": "test.automation",
                            "data": "{{ { 'foo': 'bar' } }}",
                        },
                    }
                },
            )
        ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data["foo"]).to_equal("bar")


@test
async def service_specify_data(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test service data."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }} - "
                                "{{ trigger.event.event_type }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be_truthy()

    time = dt_util.utcnow()

    with patch("homeassistant.helpers.script.utcnow", return_value=time):
        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["some"]).to_equal("event - test_event")
    state = hass.states.get("automation.hello")
    expect(state is not None).to_be(True)
    expect(state.attributes.get("last_triggered")).to_equal(time)


@test
async def service_specify_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test service data."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get(ATTR_ENTITY_ID)).to_equal(["hello.world"])


@test
async def service_specify_entity_id_list(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test service data."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "entity_id": ["hello.world", "hello.world2"],
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get(ATTR_ENTITY_ID)).to_equal(["hello.world", "hello.world2"])


@test
async def two_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test triggers."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": [
                        {"platform": "event", "event_type": "test_event"},
                        {"platform": "state", "entity_id": "test.entity"},
                    ],
                    "action": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    hass.states.async_set("test.entity", "hello")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)


@test
async def two_conditions_with_and(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test two and conditions."""
    entity_id = "test.entity"
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "triggers": [{"platform": "event", "event_type": "test_event"}],
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": entity_id,
                            "state": "100",
                        },
                        {
                            "condition": "numeric_state",
                            "entity_id": entity_id,
                            "below": 150,
                        },
                    ],
                    "actions": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entity_id, 100)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.states.async_set(entity_id, 101)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.states.async_set(entity_id, 151)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def shorthand_conditions_template(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test shorthand nation form in conditions."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "triggers": [{"platform": "event", "event_type": "test_event"}],
                    "conditions": "{{ is_state('test.entity', 'hello') }}",
                    "actions": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set("test.entity", "hello")
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.states.async_set("test.entity", "goodbye")
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def automation_list_setting(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Event is not a valid condition."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "action": {"action": "test.automation"},
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_2",
                        },
                        "action": {"action": "test.automation"},
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    hass.bus.async_fire("test_event_2")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)


@test
async def automation_calling_two_actions(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test if we can call two actions from automation async definition."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": [
                        {"action": "test.automation", "data": {"position": 0}},
                        {"action": "test.automation", "data": {"position": 1}},
                    ],
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)
    expect(calls[0].data["position"]).to_equal(0)
    expect(calls[1].data["position"]).to_equal(1)


@test
async def shared_context(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test that the shared context is passed down the chain."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "alias": "hello",
                        "trigger": {"platform": "event", "event_type": "test_event"},
                        "action": {"event": "test_event2"},
                    },
                    {
                        "alias": "bye",
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event2",
                        },
                        "action": {"action": "test.automation"},
                    },
                ]
            },
        )
    ).to_be_truthy()

    context = Context()
    first_automation_listener = Mock()
    event_mock = Mock()

    hass.bus.async_listen("test_event2", first_automation_listener)
    hass.bus.async_listen(EVENT_AUTOMATION_TRIGGERED, event_mock)
    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()

    expect(first_automation_listener.call_count).to_equal(1)
    expect(event_mock.call_count).to_equal(2)

    args, _ = event_mock.call_args_list[0]
    first_trigger_context = args[0].context
    expect(first_trigger_context.parent_id).to_equal(context.id)
    expect(args[0].data.get(ATTR_NAME) is not None).to_be(True)
    expect(args[0].data.get(ATTR_ENTITY_ID) is not None).to_be(True)
    expect(args[0].data.get(ATTR_SOURCE) is not None).to_be(True)

    args, _ = first_automation_listener.call_args
    expect(args[0].context is first_trigger_context).to_be(True)

    state = hass.states.get("automation.hello")
    expect(state is not None).to_be(True)
    expect(state.context is first_trigger_context).to_be(True)

    args, _ = event_mock.call_args_list[1]
    second_trigger_context = args[0].context
    expect(second_trigger_context.parent_id).to_equal(first_trigger_context.id)
    expect(args[0].data.get(ATTR_NAME) is not None).to_be(True)
    expect(args[0].data.get(ATTR_ENTITY_ID) is not None).to_be(True)
    expect(args[0].data.get(ATTR_SOURCE) is not None).to_be(True)

    expect(len(calls)).to_equal(1)
    expect(calls[0].context is second_trigger_context).to_be(True)


@test
async def services(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test the automation services for turning entities on/off."""
    entity_id = "automation.hello"

    expect(hass.states.get(entity_id)).to_be(None)
    expect(automation.is_on(hass, entity_id)).to_be(False)

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    expect(hass.states.get(entity_id) is not None).to_be(True)
    expect(automation.is_on(hass, entity_id)).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    expect(automation.is_on(hass, entity_id)).to_be(False)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    expect(automation.is_on(hass, entity_id)).to_be(True)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(automation.is_on(hass, entity_id)).to_be(False)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(len(calls)).to_equal(3)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TRIGGER,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(len(calls)).to_equal(4)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(automation.is_on(hass, entity_id)).to_be(True)
