"""The tests for the Event automation."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

from ._fixtures import service_calls, setup_comp

from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture, mock_network


@fixture
def context_with_user() -> Context:
    """Create a context with default user_id."""
    return Context(user_id="test_user_id")


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp),
) -> int:
    """Anchor fixture - autouse setup_comp and mock_network for every test."""
    return 0


@test
async def if_fires_on_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events."""
    context = Context()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[0].data["id"]).to_equal(0)


@test
async def if_fires_on_templated_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events."""
    context = Context()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"event_type": "test_event"},
                    "trigger": {"platform": "event", "event_type": "{{event_type}}"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_multiple_events(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events."""
    context = Context()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": ["test_event", "test2_event"],
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()
    hass.bus.async_fire("test2_event", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[0].context.parent_id).to_equal(context.id)
    expect(service_calls[1].context.parent_id).to_equal(context.id)


@test
async def if_fires_on_event_extra_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test the firing of events still matches with event data and context."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.bus.async_fire(
        "test_event", {"extra_key": "extra_data"}, context=context_with_user
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_event_with_data_and_context(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test the firing of events with data and context."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {
                            "some_attr": "some_value",
                            "second_attr": "second_value",
                        },
                        "context": {"user_id": context_with_user.user_id},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value", "second_attr": "second_value"},
        context=context_with_user,
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value"},
        context=context_with_user,
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)  # No new call

    hass.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value", "second_attr": "second_value"},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_event_with_templated_data_and_context(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test the firing of events with templated data and context."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {
                        "attr_1_val": "milk",
                        "attr_2_val": "beer",
                        "user_id": context_with_user.user_id,
                    },
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {
                            "attr_1": "{{attr_1_val}}",
                            "attr_2": "{{attr_2_val}}",
                        },
                        "context": {"user_id": "{{user_id}}"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value", "attr_2": "beer"},
        context=context_with_user,
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value"},
        context=context_with_user,
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)  # No new call

    hass.bus.async_fire(
        "test_event",
        {"attr_1": "milk", "another": "value", "attr_2": "beer"},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_event_with_empty_data_and_context_config(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test the firing of events with empty data and context config.

    The frontend automation editor can produce configurations with an
    empty dict for event_data instead of no key.
    """
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {},
                        "context": {},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire(
        "test_event",
        {"some_attr": "some_value", "another": "value"},
        context=context_with_user,
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_event_with_nested_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events with nested data.

    This test exercises the slow path of using vol.Schema to validate
    matching event data.
    """
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {"parent_attr": {"some_attr": "some_value"}},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire(
        "test_event", {"parent_attr": {"some_attr": "some_value", "another": "value"}}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_event_with_empty_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events with empty data.

    This test exercises the fast path to validate matching event data.
    """
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)
    hass.bus.async_fire("test_event", {"any_attr": {}})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_on_sample_zha_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events with a sample zha event.

    This test exercises the fast path to validate matching event data.
    """
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "zha_event",
                        "event_data": {
                            "device_ieee": "00:15:8d:00:02:93:04:11",
                            "command": "attribute_updated",
                            "args": {
                                "attribute_id": 0,
                                "attribute_name": "on_off",
                                "value": True,
                            },
                        },
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire(
        "zha_event",
        {
            "device_ieee": "00:15:8d:00:02:93:04:11",
            "unique_id": "00:15:8d:00:02:93:04:11:1:0x0006",
            "endpoint_id": 1,
            "cluster_id": 6,
            "command": "attribute_updated",
            "args": {"attribute_id": 0, "attribute_name": "on_off", "value": True},
        },
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.bus.async_fire(
        "zha_event",
        {
            "device_ieee": "00:15:8d:00:02:93:04:11",
            "unique_id": "00:15:8d:00:02:93:04:11:1:0x0006",
            "endpoint_id": 1,
            "cluster_id": 6,
            "command": "attribute_updated",
            "args": {"attribute_id": 0, "attribute_name": "on_off", "value": False},
        },
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_not_fires_if_event_data_not_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test firing of event if no data match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {"some_attr": "some_value"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", {"some_attr": "some_other_value"})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_not_fires_if_event_context_not_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test firing of event if no context match."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "context": {"user_id": "some_user"},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", {}, context=context_with_user)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)


@test
async def if_fires_on_multiple_user_ids(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    context_with_user: Context = Depends(context_with_user),
) -> None:
    """Test the firing of event when the trigger has multiple user ids.

    This test exercises the slow path of using vol.Schema to validate
    matching event context.
    """
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {},
                        "context": {
                            "user_id": [context_with_user.user_id, "another id"]
                        },
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", {}, context=context_with_user)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def event_data_with_list(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the (non)firing of event when the data schema has lists."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {"some_attr": [1, 2]},
                        "context": {},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", {"some_attr": [1, 2]})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match a single value
    hass.bus.async_fire("test_event", {"some_attr": 1})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match a containing list
    hass.bus.async_fire("test_event", {"some_attr": [1, 2, 3]})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match if property doesn't exist at all
    hass.bus.async_fire("test_event", {"other_attr": [1, 2]})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def event_data_with_list_nested(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the (non)firing of event when the data schema has nested lists."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event",
                        "event_data": {"service_data": {"some_attr": [1, 2]}},
                        "context": {},
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", {"service_data": {"some_attr": [1, 2]}})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match a single value
    hass.bus.async_fire("test_event", {"service_data": {"some_attr": 1}})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match a containing list
    hass.bus.async_fire("test_event", {"service_data": {"some_attr": [1, 2, 3]}})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    # don't match if property doesn't exist at all
    hass.bus.async_fire("test_event", {"service_data": {"other_attr": [1, 2]}})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test.cases(
    test.case("string", event_type="state_reported"),
    test.case("list", event_type=["test_event", "state_reported"]),
)
async def state_reported_event(
    event_type: str | list[str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test triggering on state reported event."""
    context = Context()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": event_type},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    expect(
        "Unnamed automation failed to setup triggers and has been disabled: Can't "
        "listen to state_reported in event trigger for dictionary value @ "
        "data['event_type']. Got None" in caplog.text
    ).to_be(True)


@test
async def templated_state_reported_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test triggering on state reported event."""
    context = Context()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger_variables": {"event_type": "state_reported"},
                    "trigger": {"platform": "event", "event_type": "{{event_type}}"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)

    hass.bus.async_fire("test_event", context=context)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    expect(
        "Got error 'Can't listen to state_reported in event trigger' "
        "when setting up triggers for automation 0" in caplog.text
    ).to_be(True)
