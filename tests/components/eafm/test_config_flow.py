"""Tests for eafm config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test
from voluptuous.error import Invalid

from homeassistant import config_entries
from homeassistant.components.eafm import const
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_get_station, mock_get_stations

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_no_discovered_stations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_stations: AsyncMock = Depends(mock_get_stations),
) -> None:
    """Test config flow discovers no station."""
    get_stations.return_value = []
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_stations")


@test
async def flow_invalid_station(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_stations: AsyncMock = Depends(mock_get_stations),
) -> None:
    """Test config flow errors on invalid station."""
    get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    raised = False
    try:
        await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"station": "My other station"}
        )
    except Invalid:
        raised = True
    expect(raised).to_be(True)


@test
async def flow_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_stations: AsyncMock = Depends(mock_get_stations),
    get_station: AsyncMock = Depends(mock_get_station),
) -> None:
    """Test config flow discovers a station."""
    get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]
    get_station.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch("homeassistant.components.eafm.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"station": "My station - R12345"}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My station - R12345")
    expect(result["data"]).to_equal({"station": "L12345"})
