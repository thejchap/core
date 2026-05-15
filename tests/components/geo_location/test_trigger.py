"""The tests for the geolocation trigger."""

import logging

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    STATE_UNAVAILABLE,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

from ._fixtures import service_calls, setup_comp

from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture, mock_network


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
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on zone enter."""
    context = Context()
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
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
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].context.parent_id).to_equal(context.id)
    expect(calls[0].data["some"]).to_equal(
        "geo_location - geo_location.entity - hello - hello - test - 0"
    )

    # Set out of zone again so we can trigger call
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758},
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    expect(len(calls)).to_equal(2)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(2)


@test
async def if_not_fires_for_enter_on_zone_leave(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on zone leave."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": "zone.test",
                        "event": "enter",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)


@test
async def if_fires_on_zone_leave(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on zone leave."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": "zone.test",
                        "event": "leave",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)


@test
async def if_fires_on_zone_leave_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing on zone leave for unavailable entity."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": "zone.test",
                        "event": "enter",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        STATE_UNAVAILABLE,
        {"source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)


@test
async def if_not_fires_for_leave_on_zone_enter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for not firing on zone enter."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": "zone.test",
                        "event": "leave",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)


@test
async def if_fires_on_zone_appear(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if entity appears in zone."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
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
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)

    # Entity appears in zone without previously existing outside the zone.
    context = Context()
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
        context=context,
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].context.parent_id).to_equal(context.id)
    expect(calls[0].data["some"]).to_equal(
        "geo_location - geo_location.entity -  - hello - test"
    )


@test
async def if_fires_on_zone_appear_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if entity appears in zone."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
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
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)

    # Entity appears in zone without previously existing outside the zone.
    context = Context()
    hass.states.async_set(
        "geo_location.entity",
        "goodbye",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
        context=context,
    )
    await hass.async_block_till_done()

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
        context=context,
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].context.parent_id).to_equal(context.id)
    expect(calls[0].data["some"]).to_equal(
        "geo_location - geo_location.entity - goodbye - hello - test"
    )


@test
async def if_fires_on_zone_disappear(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if entity disappears from zone."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": "zone.test",
                        "event": "leave",
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
                            )
                        },
                    },
                }
            },
        )
    ).to_be(True)

    # Entity disappears from zone without new coordinates outside the zone.
    hass.states.async_remove("geo_location.entity")
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[0].data["some"]).to_equal(
        "geo_location - geo_location.entity - hello -  - test"
    )


@test
async def zone_undefined(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
    caplog_fx: LogCapture = Depends(caplog),
) -> None:
    """Test for undefined zone."""
    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564, "source": "test_source"},
    )
    await hass.async_block_till_done()

    caplog_fx.set_level(logging.WARNING)

    zone_does_not_exist = "zone.does_not_exist"
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "geo_location",
                        "source": "test_source",
                        "zone": zone_does_not_exist,
                        "event": "leave",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    hass.states.async_set(
        "geo_location.entity",
        "hello",
        {"latitude": 32.881011, "longitude": -117.234758, "source": "test_source"},
    )
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)

    expect(
        f"Unable to execute automation automation 0: Zone {zone_does_not_exist} not found"
        in caplog_fx.text
    ).to_be(True)
