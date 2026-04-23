"""Tests for the Meteoclimatic config flow."""

from collections.abc import Generator
from unittest.mock import patch

from meteoclimatic.exceptions import MeteoclimaticError, StationNotFound
from tryke import Depends, expect, fixture, test

from homeassistant.components.meteoclimatic.const import CONF_STATION_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass, mock_network

TEST_STATION_CODE = "ESCAT4300000043206B"
TEST_STATION_NAME = "Reus (Tarragona)"


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_setup() -> Generator[None]:
    """Prevent setup."""
    with patch(
        "homeassistant.components.meteoclimatic.async_setup_entry",
        return_value=True,
    ):
        yield


@test
async def user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup: None = Depends(mock_setup),
) -> None:
    """Test user config."""
    with patch(
        "homeassistant.components.meteoclimatic.config_flow.MeteoclimaticClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.get_data.return_value = {
            "station_code": TEST_STATION_CODE
        }
        weather = service_mock.return_value.weather_at_station.return_value
        weather.station.name = TEST_STATION_NAME

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_STATION_CODE: TEST_STATION_CODE},
        )
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["result"].unique_id).to_equal(TEST_STATION_CODE)
        expect(result["title"]).to_equal(TEST_STATION_NAME)
        expect(result["data"][CONF_STATION_CODE]).to_equal(TEST_STATION_CODE)


@test
async def not_found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup: None = Depends(mock_setup),
) -> None:
    """Test when we have the station code is not found."""
    with patch(
        "homeassistant.components.meteoclimatic.config_flow.MeteoclimaticClient.weather_at_station",
        side_effect=StationNotFound(TEST_STATION_CODE),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_STATION_CODE: TEST_STATION_CODE},
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("not_found")


@test
async def unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup: None = Depends(mock_setup),
) -> None:
    """Test when we have an unknown error fetching station data."""
    with patch(
        "homeassistant.components.meteoclimatic.config_flow.MeteoclimaticClient.weather_at_station",
        side_effect=MeteoclimaticError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_STATION_CODE: TEST_STATION_CODE},
        )
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("unknown")
