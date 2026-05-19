"""The tests for the sun automation (tryke port)."""

from datetime import datetime

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation, sun
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import service_calls as service_calls_fixture

from tests.common import async_fire_time_changed, mock_component
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def setup_comp(hass: HomeAssistant = Depends(hass_fixture)) -> HomeAssistant:
    """Initialize components."""
    mock_component(hass, "group")
    await async_setup_component(hass, sun.DOMAIN, {sun.DOMAIN: {}})
    return hass


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(setup_comp),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@test
async def sunset_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test the sunset trigger."""
    now = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 2, tzinfo=dt_util.UTC)

    with freeze_time(now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "sun", "event": SUN_EVENT_SUNSET},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )

        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
            blocking=True,
        )
        expect(len(service_calls)).to_equal(1)

        async_fire_time_changed(hass, trigger_time)
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)

    with freeze_time(now):
        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
            blocking=True,
        )
        expect(len(service_calls)).to_equal(2)

        async_fire_time_changed(hass, trigger_time)
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(3)
        expect(service_calls[2].data["id"]).to_equal(0)


@test
async def sunrise_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test the sunrise trigger."""
    now = datetime(2015, 9, 13, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 14, tzinfo=dt_util.UTC)

    with freeze_time(now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "sun", "event": SUN_EVENT_SUNRISE},
                    "action": {"service": "test.automation"},
                }
            },
        )

        async_fire_time_changed(hass, trigger_time)
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)


@test
async def sunset_trigger_with_offset(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test the sunset trigger with offset."""
    now = datetime(2015, 9, 15, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 2, 30, tzinfo=dt_util.UTC)

    with freeze_time(now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "sun",
                        "event": SUN_EVENT_SUNSET,
                        "offset": "0:30:00",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "{{ trigger.platform }}"
                                " - {{ trigger.event }}"
                                " - {{ trigger.offset }}"
                            )
                        },
                    },
                }
            },
        )

        async_fire_time_changed(hass, trigger_time)
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("sun - sunset - 0:30:00")


@test
async def sunrise_trigger_with_offset(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test the sunrise trigger with offset."""
    now = datetime(2015, 9, 13, 23, tzinfo=dt_util.UTC)
    trigger_time = datetime(2015, 9, 16, 13, 30, tzinfo=dt_util.UTC)

    with freeze_time(now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "sun",
                        "event": SUN_EVENT_SUNRISE,
                        "offset": "-0:30:00",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )

        async_fire_time_changed(hass, trigger_time)
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)
