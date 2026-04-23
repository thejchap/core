"""Test the NMBS config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nmbs.config_flow import CONF_EXCLUDE_VIAS
from homeassistant.components.nmbs.const import (
    CONF_STATION_FROM,
    CONF_STATION_TO,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nmbs._fixtures import (
    mock_config_entry,
    mock_nmbs_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


DUMMY_DATA: dict[str, Any] = {
    "STAT_BRUSSELS_NORTH": "BE.NMBS.008812005",
    "STAT_BRUSSELS_CENTRAL": "BE.NMBS.008813003",
    "STAT_BRUSSELS_SOUTH": "BE.NMBS.008814001",
}


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nmbs_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_SOUTH"],
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(
        "Train from Brussel-Noord/Bruxelles-Nord to Brussel-Zuid/Bruxelles-Midi"
    )
    expect(result["data"]).to_equal(
        {
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_SOUTH"],
        }
    )
    expect(result["result"].unique_id).to_equal(
        f"{DUMMY_DATA['STAT_BRUSSELS_NORTH']}_{DUMMY_DATA['STAT_BRUSSELS_SOUTH']}"
    )


@test
async def same_station(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nmbs_client),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test selecting the same station."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "same_station"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_SOUTH"],
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def abort_if_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nmbs_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting the flow if the entry already exists."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_SOUTH"],
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dont_abort_if_exists_when_vias_differs(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_nmbs_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting the flow if the entry already exists."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_STATION_FROM: DUMMY_DATA["STAT_BRUSSELS_NORTH"],
            CONF_STATION_TO: DUMMY_DATA["STAT_BRUSSELS_SOUTH"],
            CONF_EXCLUDE_VIAS: True,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def unavailable_api(
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_nmbs_client),
) -> None:
    """Test starting a flow by user and api is unavailable."""
    client.get_stations.return_value = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("api_unavailable")
