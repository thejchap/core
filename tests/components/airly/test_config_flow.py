"""Define tests for the Airly config flow."""

from http import HTTPStatus

from airly.exceptions import AirlyError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airly.const import CONF_USE_NEAREST, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, async_load_fixture, patch
from tests.hass_fixtures import aioclient_mock, hass, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker

from . import API_NEAREST_URL, API_POINT_URL


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


CONFIG = {
    CONF_NAME: "Home",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 123,
    CONF_LONGITUDE: 456,
}


@test
async def show_form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def invalid_api_key(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
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

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("wrong_location")


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that errors are shown when duplicates are added."""
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "valid_station.json", DOMAIN)
    )
    MockConfigEntry(domain=DOMAIN, unique_id="123-456", data=CONFIG).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that the user step works."""
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "valid_station.json", DOMAIN)
    )

    with patch("homeassistant.components.airly.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(CONFIG[CONF_NAME])
    expect(result["data"][CONF_LATITUDE]).to_equal(CONFIG[CONF_LATITUDE])
    expect(result["data"][CONF_LONGITUDE]).to_equal(CONFIG[CONF_LONGITUDE])
    expect(result["data"][CONF_API_KEY]).to_equal(CONFIG[CONF_API_KEY])
    expect(result["data"][CONF_USE_NEAREST] is False).to_be(True)


@test
async def create_entry_with_nearest_method(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
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

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(CONFIG[CONF_NAME])
    expect(result["data"][CONF_LATITUDE]).to_equal(CONFIG[CONF_LATITUDE])
    expect(result["data"][CONF_LONGITUDE]).to_equal(CONFIG[CONF_LONGITUDE])
    expect(result["data"][CONF_API_KEY]).to_equal(CONFIG[CONF_API_KEY])
    expect(result["data"][CONF_USE_NEAREST] is True).to_be(True)
