"""Tests for eafm config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from voluptuous.error import Invalid
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.eafm import const
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.eafm._fixtures import (
    mock_get_station,
    mock_get_stations,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def flow_no_discovered_stations(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_get_stations: AsyncMock = Depends(mock_get_stations),
) -> None:
    """Test config flow discovers no station."""
    mock_get_stations.return_value = []
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_stations")


@test
async def flow_invalid_station(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_get_stations: AsyncMock = Depends(mock_get_stations),
) -> None:
    """Test config flow errors on invalid station."""
    mock_get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

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
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_get_stations: AsyncMock = Depends(mock_get_stations),
    mock_get_station: AsyncMock = Depends(mock_get_station),
) -> None:
    """Test config flow discovers no station."""
    mock_get_stations.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]
    mock_get_station.return_value = [
        {"label": "My station", "stationReference": "L12345", "RLOIid": "R12345"}
    ]

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    with patch("homeassistant.components.eafm.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"station": "My station - R12345"}
        )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("My station - R12345")
    expect(result["data"]).to_equal(
        {
            "station": "L12345",
        }
    )
