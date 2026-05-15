"""Test Subaru device tracker."""

from copy import deepcopy
from unittest.mock import patch

from subarulink.const import LATITUDE, LONGITUDE, TIMESTAMP, VEHICLE_STATUS
from tryke import Depends, expect, fixture, test

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

from ._fixtures import ev_entry as ev_entry_fixture
from .api_responses import EXPECTED_STATE_EV_IMPERIAL, VEHICLE_STATUS_EV
from .conftest import MOCK_API_FETCH, MOCK_API_GET_DATA, advance_time_to_next_fetch

DEVICE_ID = "device_tracker.test_vehicle_2"


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def device_tracker(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test subaru device tracker entity exists and has correct info."""
    entry = entity_registry.async_get(DEVICE_ID)
    expect(bool(entry)).to_be(True)
    actual = hass.states.get(DEVICE_ID)
    expect(actual.attributes.get(ATTR_LONGITUDE)).to_equal(
        EXPECTED_STATE_EV_IMPERIAL[LONGITUDE]
    )
    expect(actual.attributes.get(ATTR_LATITUDE)).to_equal(
        EXPECTED_STATE_EV_IMPERIAL[LATITUDE]
    )


@test
async def device_tracker_none_data(
    hass: HomeAssistant = Depends(_trigger_executor),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test when location information contains None."""
    bad_status = deepcopy(VEHICLE_STATUS_EV)
    bad_status[VEHICLE_STATUS][LATITUDE] = None
    bad_status[VEHICLE_STATUS][LONGITUDE] = None
    bad_status[VEHICLE_STATUS][TIMESTAMP] = None
    with patch(MOCK_API_FETCH), patch(MOCK_API_GET_DATA, return_value=bad_status):
        advance_time_to_next_fetch(hass)
        await hass.async_block_till_done()

    actual = hass.states.get(DEVICE_ID)
    expect(bool(actual.attributes.get(ATTR_LATITUDE))).to_be(False)
    expect(bool(actual.attributes.get(ATTR_LONGITUDE))).to_be(False)


@test
async def device_tracker_missing_data(
    hass: HomeAssistant = Depends(_trigger_executor),
    ev_entry: MockConfigEntry = Depends(ev_entry_fixture),
) -> None:
    """Test when location keys are missing from vehicle status."""
    bad_status = deepcopy(VEHICLE_STATUS_EV)
    bad_status[VEHICLE_STATUS].pop(LATITUDE)
    bad_status[VEHICLE_STATUS].pop(LONGITUDE)
    bad_status[VEHICLE_STATUS].pop(TIMESTAMP)
    with patch(MOCK_API_FETCH), patch(MOCK_API_GET_DATA, return_value=bad_status):
        advance_time_to_next_fetch(hass)
        await hass.async_block_till_done()

    actual = hass.states.get(DEVICE_ID)
    expect(bool(actual.attributes.get(ATTR_LATITUDE))).to_be(False)
    expect(bool(actual.attributes.get(ATTR_LONGITUDE))).to_be(False)
