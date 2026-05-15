"""The tests for the Geofency device tracker platform."""

from http import HTTPStatus

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components.geofency import DOMAIN
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_HOME,
    STATE_NOT_HOME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import slugify

from ._fixtures import geofency_client, webhook_id

from tests.hass_fixtures import (
    device_registry,
    entity_registry,
    hass as hass_fixture,
    mock_network,
)

HOME_LATITUDE = 37.239622
HOME_LONGITUDE = -115.815811

NOT_HOME_LATITUDE = 37.239394
NOT_HOME_LONGITUDE = -115.763283

GPS_ENTER_HOME = {
    "latitude": HOME_LATITUDE,
    "longitude": HOME_LONGITUDE,
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Home",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "1",
}

GPS_EXIT_HOME = {
    "latitude": HOME_LATITUDE,
    "longitude": HOME_LONGITUDE,
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Home",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "0",
}

BEACON_ENTER_HOME = {
    "latitude": HOME_LATITUDE,
    "longitude": HOME_LONGITUDE,
    "beaconUUID": "FFEF0E83-09B2-47C8-9837-E7B563F5F556",
    "minor": "36138",
    "major": "8629",
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Home",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "1",
}

BEACON_EXIT_HOME = {
    "latitude": HOME_LATITUDE,
    "longitude": HOME_LONGITUDE,
    "beaconUUID": "FFEF0E83-09B2-47C8-9837-E7B563F5F556",
    "minor": "36138",
    "major": "8629",
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Home",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "0",
}

BEACON_ENTER_CAR = {
    "latitude": NOT_HOME_LATITUDE,
    "longitude": NOT_HOME_LONGITUDE,
    "beaconUUID": "FFEF0E83-09B2-47C8-9837-E7B563F5F556",
    "minor": "36138",
    "major": "8629",
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Car 1",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "1",
}

BEACON_EXIT_CAR = {
    "latitude": NOT_HOME_LATITUDE,
    "longitude": NOT_HOME_LONGITUDE,
    "beaconUUID": "FFEF0E83-09B2-47C8-9837-E7B563F5F556",
    "minor": "36138",
    "major": "8629",
    "device": "4A7FE356-2E9D-4264-A43F-BF80ECAEE416",
    "name": "Car 1",
    "radius": 100,
    "id": "BAAD384B-A4AE-4983-F5F5-4C2F28E68205",
    "date": "2017-08-19T10:53:53Z",
    "address": "Testing Trail 1",
    "entry": "0",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def data_validation(
    _trigger: None = Depends(_trigger_executor),
    client: TestClient = Depends(geofency_client),
    wh_id: str = Depends(webhook_id),
) -> None:
    """Test data validation."""
    url = f"/api/webhook/{wh_id}"

    # No data
    req = await client.post(url)
    expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)

    missing_attributes = ["address", "device", "entry", "latitude", "longitude", "name"]

    # missing attributes
    for attribute in missing_attributes:
        copy = GPS_ENTER_HOME.copy()
        del copy[attribute]
        req = await client.post(url, data=copy)
        expect(req.status).to_equal(HTTPStatus.UNPROCESSABLE_ENTITY)


@test
async def gps_enter_and_exit_home(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ent_reg: er.EntityRegistry = Depends(entity_registry),
    dev_reg: dr.DeviceRegistry = Depends(device_registry),
    client: TestClient = Depends(geofency_client),
    wh_id: str = Depends(webhook_id),
) -> None:
    """Test GPS based zone enter and exit."""
    url = f"/api/webhook/{wh_id}"

    # Enter the Home zone
    req = await client.post(url, data=GPS_ENTER_HOME)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(GPS_ENTER_HOME["device"])
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_HOME)

    # Exit the Home zone
    req = await client.post(url, data=GPS_EXIT_HOME)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(GPS_EXIT_HOME["device"])
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_NOT_HOME)

    # Exit the Home zone with "Send Current Position" enabled
    data = GPS_EXIT_HOME.copy()
    data["currentLatitude"] = NOT_HOME_LATITUDE
    data["currentLongitude"] = NOT_HOME_LONGITUDE

    req = await client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(GPS_EXIT_HOME["device"])
    current_latitude = hass.states.get(f"device_tracker.{device_name}").attributes[
        "latitude"
    ]
    expect(current_latitude).to_equal(NOT_HOME_LATITUDE)
    current_longitude = hass.states.get(f"device_tracker.{device_name}").attributes[
        "longitude"
    ]
    expect(current_longitude).to_equal(NOT_HOME_LONGITUDE)

    expect(len(dev_reg.devices)).to_equal(1)
    expect(len(ent_reg.entities)).to_equal(1)


@test
async def beacon_enter_and_exit_home(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: TestClient = Depends(geofency_client),
    wh_id: str = Depends(webhook_id),
) -> None:
    """Test iBeacon based zone enter and exit - a.k.a stationary iBeacon."""
    url = f"/api/webhook/{wh_id}"

    # Enter the Home zone
    req = await client.post(url, data=BEACON_ENTER_HOME)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{BEACON_ENTER_HOME['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_HOME)

    # Exit the Home zone
    req = await client.post(url, data=BEACON_EXIT_HOME)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{BEACON_ENTER_HOME['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_NOT_HOME)


@test
async def beacon_enter_and_exit_car(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: TestClient = Depends(geofency_client),
    wh_id: str = Depends(webhook_id),
) -> None:
    """Test use of mobile iBeacon."""
    url = f"/api/webhook/{wh_id}"

    # Enter the Car away from Home zone
    req = await client.post(url, data=BEACON_ENTER_CAR)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{BEACON_ENTER_CAR['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_NOT_HOME)

    # Exit the Car away from Home zone
    req = await client.post(url, data=BEACON_EXIT_CAR)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{BEACON_ENTER_CAR['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_NOT_HOME)

    # Enter the Car in the Home zone
    data = BEACON_ENTER_CAR.copy()
    data["latitude"] = HOME_LATITUDE
    data["longitude"] = HOME_LONGITUDE
    req = await client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{data['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_HOME)

    # Exit the Car in the Home zone
    req = await client.post(url, data=data)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(f"beacon_{data['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    expect(state_name).to_equal(STATE_HOME)


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: TestClient = Depends(geofency_client),
    wh_id: str = Depends(webhook_id),
) -> None:
    """Test that the appropriate dispatch signals are added and removed."""
    url = f"/api/webhook/{wh_id}"

    # Enter the Home zone
    req = await client.post(url, data=GPS_ENTER_HOME)
    await hass.async_block_till_done()
    expect(req.status).to_equal(HTTPStatus.OK)
    device_name = slugify(GPS_ENTER_HOME["device"])
    state_1 = hass.states.get(f"device_tracker.{device_name}")
    expect(state_1.state).to_equal(STATE_HOME)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(len(entry.runtime_data)).to_equal(1)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    state_2 = hass.states.get(f"device_tracker.{device_name}")
    expect(state_2 is not None).to_be(True)
    expect(state_1 is not state_2).to_be(True)

    expect(state_2.state).to_equal(STATE_HOME)
    expect(state_2.attributes[ATTR_LATITUDE]).to_equal(HOME_LATITUDE)
    expect(state_2.attributes[ATTR_LONGITUDE]).to_equal(HOME_LONGITUDE)
