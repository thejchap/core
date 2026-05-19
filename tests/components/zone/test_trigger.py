"""The tests for the location automation (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import service_calls as service_calls_fixture, setup_comp

from tests.hass_fixtures import (
    LogCapture,
    caplog,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp),
) -> None:
    """Anchor fixture - autouse setup_comp for every test."""


@test
async def if_fires_on_zone_enter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for firing on zone enter."""
    context = Context()
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.test",
                        "event": "enter",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.zone.name }}"
                                " - {{ trigger.id }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)
    expect(service_calls[0].data["some"]).to_equal(
        "zone - test.entity - hello - hello - test - 0"
    )

    # Set out of zone again so we can trigger call
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_on_zone_enter_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for firing on zone enter when device is specified by entity registry id."""
    context = Context()

    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="entity"
    )
    expect(entry.entity_id).to_equal("test.entity")

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "zone",
                        "entity_id": entry.id,
                        "zone": "zone.test",
                        "event": "enter",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.entity_id }}"
                                " - {{ trigger.from_state.state }}"
                                " - {{ trigger.to_state.state }}"
                                " - {{ trigger.zone.name }}"
                                " - {{ trigger.id }}"
                            )
                        },
                    },
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].context.parent_id).to_equal(context.id)
    expect(service_calls[0].data["some"]).to_equal(
        "zone - test.entity - hello - hello - test - 0"
    )

    # Set out of zone again so we can trigger call
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)


@test
async def if_not_fires_for_enter_on_zone_leave(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for not firing on zone leave."""
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.test",
                        "event": "enter",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(0)


@test
async def if_fires_on_zone_leave(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for firing on zone leave."""
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.test",
                        "event": "leave",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)


@test
async def if_not_fires_for_leave_on_zone_enter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for not firing on zone enter."""
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.test",
                        "event": "leave",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(0)


@test
async def zone_condition(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for zone condition."""
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "condition": {
                        "condition": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.test",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def unknown_zone(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog_fx: LogCapture = Depends(caplog),
) -> None:
    """Test for firing on zone enter."""
    context = Context()
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "My Automation",
                    "trigger": {
                        "platform": "zone",
                        "entity_id": "test.entity",
                        "zone": "zone.no_such_zone",
                        "event": "enter",
                    },
                    "action": {
                        "service": "test.automation",
                    },
                }
            },
        )
    ).to_be_truthy()

    expect(
        "Automation 'My Automation' is referencing non-existing zone"
        " 'zone.no_such_zone' in a zone trigger"
        not in caplog_fx.text
    ).to_be_truthy()

    hass.states.async_set(
        "test.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await hass.async_block_till_done()

    expect(
        "Automation 'My Automation' is referencing non-existing zone"
        " 'zone.no_such_zone' in a zone trigger"
        in caplog_fx.text
    ).to_be_truthy()
