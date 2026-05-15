"""The tests for the Home Assistant SpaceAPI component."""

from http import HTTPStatus

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components.spaceapi import (
    ATTR_SENSOR_LOCATION,
    DOMAIN,
    SPACEAPI_VERSION,
    URL_API_SPACEAPI,
)
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client,
    hass_client_no_auth,
    mock_network,
)
from tests.typing import ClientSessionGenerator

CONFIG = {
    DOMAIN: {
        "space": "Home",
        "logo": "https://home-assistant.io/logo.png",
        "url": "https://home-assistant.io",
        "location": {"address": "In your Home"},
        "contact": {"email": "hello@home-assistant.io"},
        "issue_report_channels": ["email"],
        "state": {
            "entity_id": "test.test_door",
            "icon_open": "https://home-assistant.io/open.png",
            "icon_closed": "https://home-assistant.io/close.png",
        },
        "sensors": {
            "temperature": ["test.temp1", "test.temp2", "test.temp3"],
            "humidity": ["test.hum1"],
        },
        "spacefed": {"spacenet": True, "spacesaml": False, "spacephone": True},
        "cam": ["https://home-assistant.io/cam1", "https://home-assistant.io/cam2"],
        "stream": {
            "m4": "https://home-assistant.io/m4",
            "mjpeg": "https://home-assistant.io/mjpeg",
            "ustream": "https://home-assistant.io/ustream",
        },
        "feeds": {
            "blog": {"url": "https://home-assistant.io/blog"},
            "wiki": {"type": "mediawiki", "url": "https://home-assistant.io/wiki"},
            "calendar": {"type": "ical", "url": "https://home-assistant.io/calendar"},
            "flicker": {"url": "https://www.flickr.com/photos/home-assistant"},
        },
        "cache": {"schedule": "m.02"},
        "projects": [
            "https://home-assistant.io/projects/1",
            "https://home-assistant.io/projects/2",
            "https://home-assistant.io/projects/3",
        ],
        "radio_show": [
            {
                "name": "Radioshow",
                "url": "https://home-assistant.io/radio",
                "type": "ogg",
                "start": "2019-09-02T10:00Z",
                "end": "2019-09-02T12:00Z",
            }
        ],
    }
}

SENSOR_OUTPUT = {
    "temperature": [
        {
            "location": "Home",
            "name": "temp1",
            "unit": UnitOfTemperature.CELSIUS,
            "value": 25.0,
        },
        {
            "location": "outside",
            "name": "temp2",
            "unit": UnitOfTemperature.CELSIUS,
            "value": 23.0,
        },
        {
            "location": "Home",
            "name": "temp3",
            "unit": UnitOfTemperature.CELSIUS,
            "value": None,
        },
    ],
    "humidity": [
        {"location": "Home", "name": "hum1", "unit": PERCENTAGE, "value": 88.0}
    ],
}


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
async def mock_client(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client),
) -> TestClient:
    """Start the Home Assistant HTTP component."""
    await async_setup_component(hass, "spaceapi", CONFIG)

    hass.states.async_set(
        "test.temp1",
        25,
        attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "test.temp2",
        23,
        attributes={
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
            ATTR_SENSOR_LOCATION: "outside",
        },
    )
    hass.states.async_set(
        "test.temp3",
        "foo",
        attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "test.temp3",
        "foo",
        attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "test.hum1", 88, attributes={ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE}
    )

    return await hass_client()


@test
async def spaceapi_get(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test response after start-up Home Assistant."""
    resp = await mock_client.get(URL_API_SPACEAPI)
    expect(resp.status).to_equal(HTTPStatus.OK)

    data = await resp.json()

    expect(data["api"]).to_equal(SPACEAPI_VERSION)
    expect(data["space"]).to_equal("Home")
    expect(data["contact"]["email"]).to_equal("hello@home-assistant.io")
    expect(data["location"]["address"]).to_equal("In your Home")
    expect(data["location"]["lat"]).to_equal(32.87336)
    expect(data["location"]["lon"]).to_equal(-117.22743)
    expect(data["state"]["open"]).to_equal("null")
    expect(data["state"]["icon"]["open"]).to_equal("https://home-assistant.io/open.png")
    expect(data["state"]["icon"]["closed"]).to_equal(
        "https://home-assistant.io/close.png"
    )
    expect(data["spacefed"]["spacenet"]).to_equal(bool(1))
    expect(data["spacefed"]["spacesaml"]).to_equal(bool(0))
    expect(data["spacefed"]["spacephone"]).to_equal(bool(1))
    expect(data["cam"][0]).to_equal("https://home-assistant.io/cam1")
    expect(data["cam"][1]).to_equal("https://home-assistant.io/cam2")
    expect(data["stream"]["m4"]).to_equal("https://home-assistant.io/m4")
    expect(data["stream"]["mjpeg"]).to_equal("https://home-assistant.io/mjpeg")
    expect(data["stream"]["ustream"]).to_equal("https://home-assistant.io/ustream")
    expect(data["feeds"]["blog"]["url"]).to_equal("https://home-assistant.io/blog")
    expect(data["feeds"]["wiki"]["type"]).to_equal("mediawiki")
    expect(data["feeds"]["wiki"]["url"]).to_equal("https://home-assistant.io/wiki")
    expect(data["feeds"]["calendar"]["type"]).to_equal("ical")
    expect(data["feeds"]["calendar"]["url"]).to_equal(
        "https://home-assistant.io/calendar"
    )
    expect(data["feeds"]["flicker"]["url"]).to_equal(
        "https://www.flickr.com/photos/home-assistant"
    )
    expect(data["cache"]["schedule"]).to_equal("m.02")
    expect(data["projects"][0]).to_equal("https://home-assistant.io/projects/1")
    expect(data["projects"][1]).to_equal("https://home-assistant.io/projects/2")
    expect(data["projects"][2]).to_equal("https://home-assistant.io/projects/3")
    expect(data["radio_show"][0]["name"]).to_equal("Radioshow")
    expect(data["radio_show"][0]["url"]).to_equal("https://home-assistant.io/radio")
    expect(data["radio_show"][0]["type"]).to_equal("ogg")
    expect(data["radio_show"][0]["start"]).to_equal("2019-09-02T10:00Z")
    expect(data["radio_show"][0]["end"]).to_equal("2019-09-02T12:00Z")


@test
async def spaceapi_state_get(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test response if the state entity was set."""
    hass.states.async_set("test.test_door", True)

    resp = await mock_client.get(URL_API_SPACEAPI)
    expect(resp.status).to_equal(HTTPStatus.OK)

    data = await resp.json()
    expect(data["state"]["open"]).to_equal(bool(1))


@test
async def spaceapi_sensors_get(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test the response for the sensors."""
    resp = await mock_client.get(URL_API_SPACEAPI)
    expect(resp.status).to_equal(HTTPStatus.OK)

    data = await resp.json()
    expect(data["sensors"]).to_equal(SENSOR_OUTPUT)


@test
async def spaceapi_no_auth_required(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test SpaceAPI is accessible without authentication."""
    expect(await async_setup_component(hass, "spaceapi", CONFIG)).to_be(True)

    hass.states.async_set("test.test_door", "on")

    client = await hass_client_no_auth()
    resp = await client.get(URL_API_SPACEAPI)
    expect(resp.status).to_equal(HTTPStatus.OK)

    data = await resp.json()
    expect(data["space"]).to_equal("Home")


@test
async def spaceapi_cors_headers(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test CORS headers are present on SpaceAPI responses."""
    expect(await async_setup_component(hass, "spaceapi", CONFIG)).to_be(True)

    hass.states.async_set("test.test_door", "on")

    client = await hass_client_no_auth()
    resp = await client.options(
        URL_API_SPACEAPI,
        headers={
            "origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    expect(resp.headers["Access-Control-Allow-Origin"]).to_equal("http://example.com")
    expect("GET" in resp.headers["Access-Control-Allow-Methods"]).to_be(True)
