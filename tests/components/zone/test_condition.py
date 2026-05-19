"""The tests for the location condition (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.zone import condition as zone_condition
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionError
from homeassistant.helpers import condition, config_validation as cv

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def zone_raises(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that zone raises ConditionError on errors."""
    config = {
        "condition": "zone",
        "options": {"entity_id": "device_tracker.cat", "zone": "zone.home"},
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test_cond = await condition.async_from_config(hass, config)

    async with expect_raises_async(ConditionError, match="no zone"):
        zone_condition.zone(hass, zone_ent=None, entity="sensor.any")

    async with expect_raises_async(ConditionError, match="unknown zone"):
        test_cond.async_check()

    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

    async with expect_raises_async(ConditionError, match="no entity"):
        zone_condition.zone(hass, zone_ent="zone.home", entity=None)

    async with expect_raises_async(ConditionError, match="unknown entity"):
        test_cond.async_check()

    hass.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat"},
    )

    async with expect_raises_async(ConditionError, match="latitude"):
        test_cond.async_check()

    hass.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1},
    )

    async with expect_raises_async(ConditionError, match="longitude"):
        test_cond.async_check()

    hass.states.async_set(
        "device_tracker.cat",
        "home",
        {"friendly_name": "cat", "latitude": 2.1, "longitude": 1.1},
    )

    # All okay, now test multiple failed conditions
    expect(test_cond.async_check()).to_be_truthy()

    config = {
        "condition": "zone",
        "options": {
            "entity_id": ["device_tracker.cat", "device_tracker.dog"],
            "zone": ["zone.home", "zone.work"],
        },
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test_cond = await condition.async_from_config(hass, config)

    async with expect_raises_async(ConditionError, match="dog"):
        test_cond.async_check()

    async with expect_raises_async(ConditionError, match="work"):
        test_cond.async_check()

    hass.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20, "longitude": 10, "radius": 25000},
    )

    hass.states.async_set(
        "device_tracker.dog",
        "work",
        {"friendly_name": "dog", "latitude": 20.1, "longitude": 10.1},
    )

    expect(test_cond.async_check()).to_be_truthy()


@test
async def zone_multiple_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test with multiple entities in condition."""
    config = {
        "condition": "and",
        "conditions": [
            {
                "alias": "Zone Condition",
                "condition": "zone",
                "options": {
                    "entity_id": ["device_tracker.person_1", "device_tracker.person_2"],
                    "zone": "zone.home",
                },
            },
        ],
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test_cond = await condition.async_from_config(hass, config)

    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )

    hass.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
    hass.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    expect(test_cond.async_check()).to_be_truthy()

    hass.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 20.1, "longitude": 10.1},
    )
    hass.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 2.1, "longitude": 1.1},
    )
    expect(test_cond.async_check()).to_be_falsy()

    hass.states.async_set(
        "device_tracker.person_1",
        "home",
        {"friendly_name": "person_1", "latitude": 2.1, "longitude": 1.1},
    )
    hass.states.async_set(
        "device_tracker.person_2",
        "home",
        {"friendly_name": "person_2", "latitude": 20.1, "longitude": 10.1},
    )
    expect(test_cond.async_check()).to_be_falsy()


@test
async def multiple_zones(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test with multiple entities in condition."""
    config = {
        "condition": "and",
        "conditions": [
            {
                "condition": "zone",
                "options": {
                    "entity_id": "device_tracker.person",
                    "zone": ["zone.home", "zone.work"],
                },
            },
        ],
    }
    config = cv.CONDITION_SCHEMA(config)
    config = await condition.async_validate_condition_config(hass, config)
    test_cond = await condition.async_from_config(hass, config)

    hass.states.async_set(
        "zone.home",
        "zoning",
        {"name": "home", "latitude": 2.1, "longitude": 1.1, "radius": 10},
    )
    hass.states.async_set(
        "zone.work",
        "zoning",
        {"name": "work", "latitude": 20.1, "longitude": 10.1, "radius": 10},
    )

    hass.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 2.1, "longitude": 1.1},
    )
    expect(test_cond.async_check()).to_be_truthy()

    hass.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 20.1, "longitude": 10.1},
    )
    expect(test_cond.async_check()).to_be_truthy()

    hass.states.async_set(
        "device_tracker.person",
        "home",
        {"friendly_name": "person", "latitude": 50.1, "longitude": 20.1},
    )
    expect(test_cond.async_check()).to_be_falsy()
