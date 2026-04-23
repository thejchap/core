"""Test the Environment Canada (EC) config flow."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch
import xml.etree.ElementTree as ET

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.environment_canada.const import CONF_STATION, DOMAIN
from homeassistant.const import CONF_LANGUAGE, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.environment_canada._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network

FAKE_CONFIG = {
    CONF_STATION: "123",
    CONF_LANGUAGE: "English",
    CONF_LATITUDE: 42.42,
    CONF_LONGITUDE: -42.42,
}
FAKE_TITLE = "Universal title!"
FAKE_STATIONS = [
    {"label": "Toronto, ON", "value": "123"},
    {"label": "Ottawa, ON", "value": "456"},
    {"label": "Montreal, QC", "value": "789"},
]


def mocked_ec():
    """Mock the env_canada library."""
    ec_mock = MagicMock()
    ec_mock.station_id = FAKE_CONFIG[CONF_STATION]
    ec_mock.lat = FAKE_CONFIG[CONF_LATITUDE]
    ec_mock.lon = FAKE_CONFIG[CONF_LONGITUDE]
    ec_mock.language = FAKE_CONFIG[CONF_LANGUAGE]
    ec_mock.metadata.location = FAKE_TITLE

    ec_mock.update = AsyncMock()

    return patch(
        "homeassistant.components.environment_canada.config_flow.ECWeather",
        return_value=ec_mock,
    )


def mocked_stations():
    """Mock the station list."""
    return patch(
        "homeassistant.components.environment_canada.config_flow.get_ec_sites_list",
        return_value=FAKE_STATIONS,
    )


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test creating an entry."""
    with (
        mocked_ec(),
        mocked_stations(),
        patch(
            "homeassistant.components.environment_canada.async_setup_entry",
            return_value=True,
        ),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], FAKE_CONFIG
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["data"]).to_equal(FAKE_CONFIG)
        expect(result["title"]).to_equal(FAKE_TITLE)


@test
async def create_same_entry_twice(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test duplicate entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=FAKE_CONFIG,
        unique_id="123-english",
    )
    entry.add_to_hass(hass)

    with (
        mocked_ec(),
        mocked_stations(),
        patch(
            "homeassistant.components.environment_canada.async_setup_entry",
            return_value=True,
        ),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], FAKE_CONFIG
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "not_found",
        aiohttp.ClientResponseError(Mock(), (), status=404),
        "bad_station_id",
    ),
    test.case(
        "bad_request",
        aiohttp.ClientResponseError(Mock(), (), status=400),
        "error_response",
    ),
    test.case(
        "connection", aiohttp.ClientConnectionError, "cannot_connect"
    ),
    test.case("parse_error", ET.ParseError, "bad_station_id"),
    test.case("value_error", ValueError, "unknown"),
)
async def exception_handling(
    exc: Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test exception handling."""
    with (
        mocked_stations(),
        patch(
            "homeassistant.components.environment_canada.config_flow.ECWeather",
            side_effect=exc,
        ),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {},
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal({"base": base_error})


@test
async def lat_lon_not_specified(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the import step works when coordinates are not specified."""
    with (
        mocked_ec(),
        mocked_stations(),
        patch(
            "homeassistant.components.environment_canada.async_setup_entry",
            return_value=True,
        ),
    ):
        fake_config = dict(FAKE_CONFIG)
        del fake_config[CONF_LATITUDE]
        del fake_config[CONF_LONGITUDE]
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=fake_config
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["data"]).to_equal(FAKE_CONFIG)
        expect(result["title"]).to_equal(FAKE_TITLE)


@test
async def coordinates_without_station(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test setup with coordinates but no station ID."""
    with (
        mocked_ec(),
        mocked_stations(),
        patch(
            "homeassistant.components.environment_canada.async_setup_entry",
            return_value=True,
        ),
    ):
        config_no_station = {
            CONF_LANGUAGE: "English",
            CONF_LATITUDE: 42.42,
            CONF_LONGITUDE: -42.42,
        }
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], config_no_station
        )
        await hass.async_block_till_done()
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["data"]).to_equal(FAKE_CONFIG)
        expect(result["title"]).to_equal(FAKE_TITLE)
