"""The tests for the time_pattern automation."""

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components import automation
from homeassistant.components.homeassistant.triggers import time_pattern
from homeassistant.const import ATTR_ENTITY_ID, ENTITY_MATCH_ALL, SERVICE_TURN_OFF
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import service_calls, setup_comp

from tests.common import async_fire_time_changed
from tests.hass_fixtures import freezer, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(setup_comp),
) -> int:
    """Anchor fixture - autouse setup_comp and mock_network for every test."""
    return 0


@test
async def if_fires_when_hour_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if hour is matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, hour=3
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": 0,
                        "minutes": "*",
                        "seconds": "*",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(hass, now.replace(year=now.year + 2, day=1, hour=0))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["id"]).to_equal(0)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    expect(len(service_calls)).to_equal(2)

    async_fire_time_changed(hass, now.replace(year=now.year + 1, day=1, hour=0))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_fires_when_minute_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if minutes are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, minute=30
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": 0,
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(hass, now.replace(year=now.year + 2, day=1, minute=0))

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_when_second_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if seconds are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, second=30
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": 0,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(hass, now.replace(year=now.year + 2, day=1, second=0))

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_when_second_as_string_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if seconds are matching."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, second=15
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": "30",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, time_that_will_not_match_right_away + timedelta(seconds=15)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_when_all_matches(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing if everything matches."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, hour=4
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": 1,
                        "minutes": 2,
                        "seconds": 3,
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=1, minute=2, second=3)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_periodic_seconds(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing periodically every second."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, second=1
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "*",
                        "seconds": "/10",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=0, minute=0, second=10)
    )

    await hass.async_block_till_done()
    expect(len(service_calls) >= 1).to_be(True)


@test
async def if_fires_periodic_minutes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing periodically every minute."""

    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, minute=1
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "*",
                        "minutes": "/2",
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=0, minute=2, second=0)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def if_fires_periodic_hours(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing periodically every hour."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, hour=1
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "time_pattern",
                        "hours": "/2",
                        "minutes": "*",
                        "seconds": "*",
                    },
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=2, minute=0, second=0)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)


@test
async def default_values(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test for firing at 2 minutes every hour."""
    now = dt_util.utcnow()
    time_that_will_not_match_right_away = dt_util.utcnow().replace(
        year=now.year + 1, day=1, minute=1
    )
    freezer.move_to(time_that_will_not_match_right_away)
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "time_pattern", "minutes": "2"},
                    "action": {"service": "test.automation"},
                }
            },
        )
    ).to_be(True)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=1, minute=2, second=0)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=1, minute=2, second=1)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    async_fire_time_changed(
        hass, now.replace(year=now.year + 2, day=1, hour=2, minute=2, second=0)
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
def invalid_schemas() -> None:
    """Test invalid schemas."""
    schemas: tuple[Any, ...] = (
        None,
        {},
        {"platform": "time_pattern"},
        {"platform": "time_pattern", "minutes": "/"},
        {"platform": "time_pattern", "minutes": "*/5"},
        {"platform": "time_pattern", "minutes": "/90"},
        {"platform": "time_pattern", "hours": "/0", "minutes": 10},
        {"platform": "time_pattern", "hours": 12, "minutes": 0, "seconds": 100},
    )

    for value in schemas:
        expect(lambda v=value: time_pattern.TRIGGER_SCHEMA(v)).to_raise(vol.Invalid)
