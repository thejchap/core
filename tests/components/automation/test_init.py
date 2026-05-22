"""The tests for the automation component."""

import asyncio
import logging
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.automation import (
    ATTR_SOURCE,
    DOMAIN,
    EVENT_AUTOMATION_TRIGGERED,
    SERVICE_TRIGGER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    CONF_ID,
    EVENT_HOMEASSISTANT_STARTED,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import (
    Context,
    CoreState,
    HomeAssistant,
    ServiceCall,
    State,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    assert_setup_component,
    async_mock_service,
    mock_restore_cache,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


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


@test
async def trigger_service_ignoring_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test triggers."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "test",
                    "trigger": [{"platform": "event", "event_type": "test_event"}],
                    "conditions": {
                        "condition": "numeric_state",
                        "entity_id": "non.existing",
                        "above": "1",
                    },
                    "action": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    caplog.clear()
    caplog.set_level(logging.WARNING)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    expect(len(caplog.records)).to_equal(1)
    expect(caplog.records[0].levelno).to_equal(logging.WARNING)

    await hass.services.async_call(
        "automation", "trigger", {"entity_id": "automation.test"}, blocking=True
    )
    expect(len(calls)).to_equal(1)

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": True},
        blocking=True,
    )
    expect(len(calls)).to_equal(2)

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": False},
        blocking=True,
    )
    expect(len(calls)).to_equal(2)


@test
async def reload_config_when_invalid_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test the reload config service handling invalid config."""
    with assert_setup_component(1, automation.DOMAIN):
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
                                "event": "{{ trigger.event.event_type }}"
                            },
                        },
                    }
                },
            )
        ).to_be_truthy()
    expect(hass.states.get("automation.hello") is not None).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get("event")).to_equal("test_event")

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={automation.DOMAIN: "not valid"},
    ):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)

    expect(hass.states.get("automation.hello")).to_be(None)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def reload_config_handles_load_fails(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test the reload config service."""
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
                        "data_template": {"event": "{{ trigger.event.event_type }}"},
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(hass.states.get("automation.hello") is not None).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get("event")).to_equal("test_event")

    with patch(
        "homeassistant.config.load_yaml_config_file",
        side_effect=HomeAssistantError("bla"),
    ):
        async with expect_raises_async(
            ServiceValidationError, match="Failed to load configuration: bla"
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )

    expect(hass.states.get("automation.hello") is not None).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)


@test.cases(
    test.case("no_id", extra_config={}),
    test.case("with_id", extra_config={"id": "sun"}),
)
async def reload_unchanged_does_not_stop(
    *,
    extra_config: dict[str, str],
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test that reloading does not stop unchanged running actions."""
    test_entity = "test.entity"

    config = {
        automation.DOMAIN: {
            "alias": "hello",
            "triggers": {"platform": "event", "event_type": "test_event"},
            "actions": [
                {"event": "running"},
                {"wait_template": "{{ is_state('test.entity', 'goodbye') }}"},
                {"action": "test.automation"},
            ],
        }
    }
    config[automation.DOMAIN].update(**extra_config)
    expect(
        await async_setup_component(hass, automation.DOMAIN, config)
    ).to_be_truthy()

    running = asyncio.Event()

    @callback
    def running_cb(event: Any) -> None:
        running.set()

    hass.bus.async_listen_once("running", running_cb)
    hass.states.async_set(test_entity, "hello")

    hass.bus.async_fire("test_event")
    await running.wait()
    expect(len(calls)).to_equal(0)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value=config,
    ):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)

    hass.states.async_set(test_entity, "goodbye")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)


@test.cases(
    test.case("turn_off_stop", service="turn_off_stop", expected=0),
    test.case("turn_off_no_stop", service="turn_off_no_stop", expected=1),
    test.case("reload", service="reload", expected=0),
    test.case("reload_single", service="reload_single", expected=0),
)
async def automation_stops(
    *,
    service: str,
    expected: int,
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test that turning off / reloading stops running actions as appropriate."""
    entity_id = "automation.hello"
    test_entity = "test.entity"

    config = {
        automation.DOMAIN: {
            "id": "sun",
            "alias": "hello",
            "trigger": {"platform": "event", "event_type": "test_event"},
            "action": [
                {"event": "running"},
                {"wait_template": "{{ is_state('test.entity', 'goodbye') }}"},
                {"action": "test.automation"},
            ],
        }
    }
    expect(
        await async_setup_component(hass, automation.DOMAIN, config)
    ).to_be_truthy()

    running = asyncio.Event()

    @callback
    def running_cb(event: Any) -> None:
        running.set()

    hass.bus.async_listen_once("running", running_cb)
    hass.states.async_set(test_entity, "hello")

    hass.bus.async_fire("test_event")
    await running.wait()

    if service == "turn_off_stop":
        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    elif service == "turn_off_no_stop":
        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id, automation.CONF_STOP_ACTIONS: False},
            blocking=True,
        )
    elif service == "reload":
        config[automation.DOMAIN]["alias"] = "goodbye"
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN, SERVICE_RELOAD, blocking=True
            )
    else:  # service == "reload_single"
        config[automation.DOMAIN]["alias"] = "goodbye"
        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value=config,
        ):
            await hass.services.async_call(
                automation.DOMAIN,
                SERVICE_RELOAD,
                {CONF_ID: "sun"},
                blocking=True,
            )

    hass.states.async_set(test_entity, "goodbye")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(expected)


@test
async def automation_restore_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Ensure states are restored on startup."""
    time = dt_util.utcnow()

    mock_restore_cache(
        hass,
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event_hello"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "bye",
                "trigger": {"platform": "event", "event_type": "test_event_bye"},
                "action": {"action": "test.automation"},
            },
        ]
    }

    expect(
        await async_setup_component(hass, automation.DOMAIN, config)
    ).to_be_truthy()

    state = hass.states.get("automation.hello")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes["last_triggered"]).to_be(None)

    state = hass.states.get("automation.bye")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes["last_triggered"]).to_equal(time)

    service_calls = async_mock_service(hass, "test", "automation")

    expect(automation.is_on(hass, "automation.bye")).to_be(False)

    hass.bus.async_fire("test_event_bye")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    hass.bus.async_fire("test_event_hello")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def initial_value_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test initial value off."""
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "initial_state": "off",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(False)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def initial_value_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test initial value on."""
    hass.set_state(CoreState.not_running)
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "initial_state": "on",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "entity_id": ["hello.world", "hello.world2"],
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    await hass.async_start()
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def initial_value_off_but_restore_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test initial value off and restored state is turned on."""
    hass.set_state(CoreState.not_running)
    service_calls = async_mock_service(hass, "test", "automation")
    mock_restore_cache(hass, (State("automation.hello", STATE_ON),))

    await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation", "entity_id": "hello.world"},
            }
        },
    )
    expect(automation.is_on(hass, "automation.hello")).to_be(False)

    await hass.async_start()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def initial_value_on_but_restore_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test initial value on and restored state is turned off."""
    service_calls = async_mock_service(hass, "test", "automation")
    mock_restore_cache(hass, (State("automation.hello", STATE_OFF),))

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "initial_state": "on",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def no_initial_value_and_restore_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test no initial value and restored state is turned off."""
    service_calls = async_mock_service(hass, "test", "automation")
    mock_restore_cache(hass, (State("automation.hello", STATE_OFF),))

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
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(False)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def automation_is_on_if_no_initial_state_or_restore(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test initial value is on when no initial state or restored state."""
    service_calls = async_mock_service(hass, "test", "automation")

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
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def automation_not_trigger_on_bootstrap(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test if automation is not triggered on bootstrap."""
    hass.set_state(CoreState.not_running)
    service_calls = async_mock_service(hass, "test", "automation")

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
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    expect(automation.is_on(hass, "automation.hello")).to_be(True)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data.get(ATTR_ENTITY_ID)).to_equal(["hello.world"])


@test
async def automation_with_error_in_script_2(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test automation with an error in script."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"action": None, "entity_id": "hello.world"},
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect("string value is None" in caplog.text).to_be(True)


@test
async def automation_restore_last_triggered_with_initial_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Ensure last_triggered is restored, even when initial state is set."""
    time = dt_util.utcnow()

    mock_restore_cache(
        hass,
        (
            State("automation.hello", STATE_ON),
            State("automation.bye", STATE_ON, {"last_triggered": time}),
            State("automation.solong", STATE_OFF, {"last_triggered": time}),
        ),
    )

    config = {
        automation.DOMAIN: [
            {
                "alias": "hello",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "bye",
                "initial_state": "off",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
            {
                "alias": "solong",
                "initial_state": "on",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            },
        ]
    }

    await async_setup_component(hass, automation.DOMAIN, config)

    state = hass.states.get("automation.hello")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes["last_triggered"]).to_be(None)

    state = hass.states.get("automation.bye")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes["last_triggered"]).to_equal(time)

    state = hass.states.get("automation.solong")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes["last_triggered"]).to_equal(time)


@test
async def extraction_functions_not_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions when automation is not setup."""
    expect(automation.automations_with_area(hass, "area-in-both")).to_equal([])
    expect(automation.areas_in_automation(hass, "automation.test")).to_equal([])
    expect(automation.automations_with_blueprint(hass, "blabla.yaml")).to_equal([])
    expect(automation.blueprint_in_automation(hass, "automation.test")).to_be(None)
    expect(automation.automations_with_device(hass, "device-in-both")).to_equal([])
    expect(automation.devices_in_automation(hass, "automation.test")).to_equal([])
    expect(automation.automations_with_entity(hass, "light.in_both")).to_equal([])
    expect(automation.entities_in_automation(hass, "automation.test")).to_equal([])
    expect(automation.automations_with_floor(hass, "floor-in-both")).to_equal([])
    expect(automation.floors_in_automation(hass, "automation.test")).to_equal([])
    expect(automation.automations_with_label(hass, "label-in-both")).to_equal([])
    expect(automation.labels_in_automation(hass, "automation.test")).to_equal([])


@test
async def extraction_functions_unknown_automation(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions for an unknown automation."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
    expect(automation.areas_in_automation(hass, "automation.unknown")).to_equal([])
    expect(automation.blueprint_in_automation(hass, "automation.unknown")).to_be(None)
    expect(automation.devices_in_automation(hass, "automation.unknown")).to_equal([])
    expect(automation.entities_in_automation(hass, "automation.unknown")).to_equal([])
    expect(automation.floors_in_automation(hass, "automation.unknown")).to_equal([])
    expect(automation.labels_in_automation(hass, "automation.unknown")).to_equal([])


@test
async def extraction_functions_unavailable_automation(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test extraction functions for an unavailable automation."""
    entity_id = "automation.test1"
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: [{"alias": "test1"}]},
        )
    ).to_be_truthy()
    expect(hass.states.get(entity_id).state).to_equal(STATE_UNAVAILABLE)
    expect(automation.automations_with_area(hass, "area-in-both")).to_equal([])
    expect(automation.areas_in_automation(hass, entity_id)).to_equal([])
    expect(automation.automations_with_blueprint(hass, "blabla.yaml")).to_equal([])
    expect(automation.blueprint_in_automation(hass, entity_id)).to_be(None)
    expect(automation.automations_with_device(hass, "device-in-both")).to_equal([])
    expect(automation.devices_in_automation(hass, entity_id)).to_equal([])
    expect(automation.automations_with_entity(hass, "light.in_both")).to_equal([])
    expect(automation.entities_in_automation(hass, entity_id)).to_equal([])
    expect(automation.automations_with_floor(hass, "floor-in-both")).to_equal([])
    expect(automation.floors_in_automation(hass, entity_id)).to_equal([])
    expect(automation.automations_with_label(hass, "label-in-both")).to_equal([])
    expect(automation.labels_in_automation(hass, entity_id)).to_equal([])


@test
async def automation_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test automation variables."""
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "variables": {
                            "test_var": "defined_in_config",
                            "event_type": "{{ trigger.event.event_type }}",
                            "this_variables": "{{this.entity_id}}",
                        },
                        "triggers": {"trigger": "event", "event_type": "test_event"},
                        "actions": {
                            "action": "test.automation",
                            "data": {
                                "value": "{{ test_var }}",
                                "event_type": "{{ event_type }}",
                                "this_template": "{{this.entity_id}}",
                                "this_variables": "{{this_variables}}",
                            },
                        },
                    },
                    {
                        "variables": {"test_var": "defined_in_config"},
                        "trigger": {"trigger": "event", "event_type": "test_event_2"},
                        "conditions": {
                            "condition": "template",
                            "value_template": (
                                "{{ trigger.event.data.pass_condition }}"
                            ),
                        },
                        "actions": {"action": "test.automation"},
                    },
                    {
                        "variables": {
                            "test_var": "{{ trigger.event.data.break + 1 }}",
                        },
                        "triggers": {"trigger": "event", "event_type": "test_event_3"},
                        "actions": {"action": "test.automation"},
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["value"]).to_equal("defined_in_config")
    expect(service_calls[0].data["event_type"]).to_equal("test_event")
    expect(service_calls[0].data.get("this_template")).to_equal(
        "automation.automation_0"
    )
    expect(service_calls[0].data.get("this_variables")).to_equal(
        "automation.automation_0"
    )
    expect("Error rendering variables" in caplog.text).to_be(False)

    hass.bus.async_fire("test_event_2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.bus.async_fire("test_event_2", {"pass_condition": True})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)

    expect("Error rendering variables" in caplog.text).to_be(False)
    hass.bus.async_fire("test_event_3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect("Error rendering variables" in caplog.text).to_be(True)

    hass.bus.async_fire("test_event_3", {"break": 0})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)


@test
async def automation_trigger_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test automation trigger variables."""
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "variables": {
                            "event_type": "{{ trigger.event.event_type }}",
                        },
                        "trigger_variables": {"test_var": "defined_in_config"},
                        "trigger": {"trigger": "event", "event_type": "test_event"},
                        "action": {
                            "action": "test.automation",
                            "data": {
                                "value": "{{ test_var }}",
                                "event_type": "{{ event_type }}",
                            },
                        },
                    },
                    {
                        "variables": {
                            "event_type": "{{ trigger.event.event_type }}",
                            "test_var": "overridden_in_config",
                        },
                        "trigger_variables": {
                            "test_var": "defined_in_config",
                            "this_trigger_variables": "{{this.entity_id}}",
                        },
                        "trigger": {"trigger": "event", "event_type": "test_event_2"},
                        "action": {
                            "action": "test.automation",
                            "data": {
                                "value": "{{ test_var }}",
                                "event_type": "{{ event_type }}",
                                "this_template": "{{this.entity_id}}",
                                "this_trigger_variables": (
                                    "{{this_trigger_variables}}"
                                ),
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["value"]).to_equal("defined_in_config")
    expect(service_calls[0].data["event_type"]).to_equal("test_event")

    hass.bus.async_fire("test_event_2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["value"]).to_equal("overridden_in_config")
    expect(service_calls[1].data["event_type"]).to_equal("test_event_2")
    expect(service_calls[1].data.get("this_template")).to_equal(
        "automation.automation_1"
    )
    expect(service_calls[1].data.get("this_trigger_variables")).to_equal(
        "automation.automation_1"
    )
    expect("Error rendering variables" in caplog.text).to_be(False)


@test
async def automation_bad_trigger_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test automation trigger variables accessing hass is rejected."""
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger_variables": {
                            "test_var": "{{ states('foo.bar') }}",
                        },
                        "trigger": {"trigger": "event", "event_type": "test_event"},
                        "action": {"action": "test.automation"},
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.bus.async_fire("test_event")
    expect(
        "Use of 'states' is not supported in limited templates" in caplog.text
    ).to_be(True)

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def automation_this_var_always(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test automation always has reference to this."""
    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"trigger": "event", "event_type": "test_event"},
                        "action": {
                            "action": "test.automation",
                            "data": {"this_template": "{{this.entity_id}}"},
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data.get("this_template")).to_equal(
        "automation.automation_0"
    )
    expect("Error rendering variables" in caplog.text).to_be(False)


@test
async def trigger_service(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test the automation trigger service."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"trigger": "event", "event_type": "test_event"},
                    "action": {
                        "action": "test.automation",
                        "data_template": {"trigger": "{{ trigger }}"},
                    },
                }
            },
        )
    ).to_be_truthy()
    context = Context()
    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.hello"},
        blocking=True,
        context=context,
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get("trigger")).to_equal({"platform": None})
    expect(calls[0].context.parent_id is context.id).to_be(True)


@test
async def trigger_condition_implicit_id(
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
                        {"trigger": "event", "event_type": "test_event1"},
                        {"trigger": "event", "event_type": "test_event2"},
                        {"trigger": "event", "event_type": "test_event3"},
                    ],
                    "action": {
                        "choose": [
                            {
                                "conditions": {
                                    "condition": "trigger",
                                    "id": [0, "2"],
                                },
                                "sequence": {
                                    "action": "test.automation",
                                    "data": {"param": "one"},
                                },
                            },
                            {
                                "conditions": {"condition": "trigger", "id": "1"},
                                "sequence": {
                                    "action": "test.automation",
                                    "data": {"param": "two"},
                                },
                            },
                        ]
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[-1].data.get("param")).to_equal("one")

    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(calls[-1].data.get("param")).to_equal("two")

    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(3)
    expect(calls[-1].data.get("param")).to_equal("one")


@test
async def trigger_condition_explicit_id(
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
                        {
                            "trigger": "event",
                            "event_type": "test_event1",
                            "id": "one",
                        },
                        {
                            "trigger": "event",
                            "event_type": "test_event2",
                            "id": "two",
                        },
                    ],
                    "action": {
                        "choose": [
                            {
                                "conditions": {"condition": "trigger", "id": "one"},
                                "sequence": {
                                    "action": "test.automation",
                                    "data": {"param": "one"},
                                },
                            },
                            {
                                "conditions": {"condition": "trigger", "id": "two"},
                                "sequence": {
                                    "action": "test.automation",
                                    "data": {"param": "two"},
                                },
                            },
                        ]
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[-1].data.get("param")).to_equal("one")

    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
    expect(calls[-1].data.get("param")).to_equal("two")


@test
async def action_backward_compatibility(
    hass: HomeAssistant = Depends(_trigger_executor),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test we can still use old-style automations."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"trigger": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "template",
                        "value_template": "{{ True }}",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                        "data": {"event": "{{ trigger.event.event_type }}"},
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get(ATTR_ENTITY_ID)).to_equal(["hello.world"])
    expect(calls[0].data.get("event")).to_equal("test_event")


@test.cases(
    test.case(
        "trigger_and_triggers",
        config={
            "trigger": {"platform": "event", "event_type": "test_event"},
            "triggers": {"platform": "event", "event_type": "test_event2"},
            "actions": [],
        },
        message=(
            "Cannot specify both 'trigger' and 'triggers'. "
            "Please use 'triggers' only."
        ),
    ),
    test.case(
        "condition_and_conditions",
        config={
            "trigger": {"platform": "event", "event_type": "test_event"},
            "condition": {
                "condition": "template",
                "value_template": "{{ True }}",
            },
            "conditions": {
                "condition": "template",
                "value_template": "{{ True }}",
            },
        },
        message=(
            "Cannot specify both 'condition' and 'conditions'. "
            "Please use 'conditions' only."
        ),
    ),
    test.case(
        "action_and_actions",
        config={
            "trigger": {"platform": "event", "event_type": "test_event"},
            "action": {"service": "test.automation", "entity_id": "hello.world"},
            "actions": {"service": "test.automation", "entity_id": "hello.world"},
        },
        message=(
            "Cannot specify both 'action' and 'actions'. "
            "Please use 'actions' only."
        ),
    ),
    test.case(
        "platform_and_trigger",
        config={
            "trigger": {
                "platform": "event",
                "trigger": "event",
                "event_type": "test_event2",
            },
            "action": [],
        },
        message=(
            "Cannot specify both 'platform' and 'trigger'. "
            "Please use 'trigger' only."
        ),
    ),
)
async def invalid_configuration(
    *,
    config: dict[str, Any],
    message: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test for invalid automation configurations."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {automation.DOMAIN: config},
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(message in caplog.text).to_be(True)


@test.cases(
    test.case("trigger_key", trigger_key="trigger"),
    test.case("platform_key", trigger_key="platform"),
)
async def valid_configuration(
    *,
    trigger_key: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test for valid automation configurations."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "triggers": {
                        trigger_key: "event",
                        "event_type": "test_event2",
                    },
                    "action": [],
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()


@test
async def automation_changed_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    calls: list[ServiceCall] = Depends(calls),
) -> None:
    """Test that an automation still works after its entity_id is changed."""
    entry = entity_registry.async_get_or_create(
        "automation", "automation", "test_automation"
    )
    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="automation.custom_id"
    )
    expect(entry.entity_id).to_equal("automation.custom_id")

    hass.states.async_set("binary_sensor.test", "on")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "id": "test_automation",
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "state",
                        "entity_id": "binary_sensor.test",
                        "state": "on",
                    },
                    "action": {"action": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)

    entry = entity_registry.async_update_entity(
        entry.entity_id, new_entity_id="automation.custom_id_2"
    )
    expect(entry.entity_id).to_equal("automation.custom_id_2")
    await hass.async_block_till_done()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(2)
