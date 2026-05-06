"""Define tests for the Airly config flow."""

from http import HTTPStatus

from airly.exceptions import AirlyError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airly.const import CONF_USE_NEAREST, DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import API_NEAREST_URL, API_POINT_URL

from tests.common import MockConfigEntry, async_load_fixture, patch
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

CONFIG = {
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 123,
    CONF_LONGITUDE: 456,
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def invalid_api_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that errors are shown when API key is invalid."""
    aioclient_mock.get(
        API_POINT_URL,
        exc=AirlyError(
            HTTPStatus.UNAUTHORIZED, {"message": "Invalid authentication credentials"}
        ),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["errors"]).to_equal({"base": "invalid_api_key"})


@test
async def invalid_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that errors are shown when location is invalid."""
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "no_station.json", DOMAIN)
    )

    aioclient_mock.get(
        API_NEAREST_URL,
        exc=AirlyError(HTTPStatus.NOT_FOUND, {"message": "Installation was not found"}),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["errors"]).to_equal({"base": "wrong_location"})


@test
async def invalid_location_for_point_and_nearest(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test an abort when the location is wrong for the point and nearest methods."""

    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "no_station.json", DOMAIN)
    )

    aioclient_mock.get(
        API_NEAREST_URL, text=await async_load_fixture(hass, "no_station.json", DOMAIN)
    )

    with patch("homeassistant.components.airly.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_location")


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that errors are shown when duplicates are added."""
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "valid_station.json", DOMAIN)
    )
    MockConfigEntry(domain=DOMAIN, unique_id="123-456", data=CONFIG).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that the user step works."""
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "valid_station.json", DOMAIN)
    )

    with patch("homeassistant.components.airly.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_LATITUDE]).to_equal(CONFIG[CONF_LATITUDE])
    expect(result["data"][CONF_LONGITUDE]).to_equal(CONFIG[CONF_LONGITUDE])
    expect(result["data"][CONF_API_KEY]).to_equal(CONFIG[CONF_API_KEY])
    expect(result["data"][CONF_USE_NEAREST]).to_be(False)


@test
async def create_entry_with_nearest_method(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that the user step works with nearest method."""

    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "no_station.json", DOMAIN)
    )

    aioclient_mock.get(
        API_NEAREST_URL,
        text=await async_load_fixture(hass, "valid_station.json", DOMAIN),
    )

    with patch("homeassistant.components.airly.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"][CONF_LATITUDE]).to_equal(CONFIG[CONF_LATITUDE])
    expect(result["data"][CONF_LONGITUDE]).to_equal(CONFIG[CONF_LONGITUDE])
    expect(result["data"][CONF_API_KEY]).to_equal(CONFIG[CONF_API_KEY])
    expect(result["data"][CONF_USE_NEAREST]).to_be(True)
