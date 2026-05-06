"""Test the Ambient Weather Network config flow."""

from typing import Any
from unittest.mock import AsyncMock, patch

from aioambient import OpenAPI
from tryke import Depends, expect, fixture, test

from homeassistant.components.ambient_network.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    aioambient,
    config_entry_aa,
    devices_by_location,
    mock_setup_entry,
    open_api,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def happy_path(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: OpenAPI = Depends(open_api),
    _aioambient: None = Depends(aioambient),
    devices: list[dict[str, Any]] = Depends(devices_by_location),
    config_entry: MockConfigEntry = Depends(config_entry_aa),
) -> None:
    """Test the happy path."""

    setup_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(setup_result["type"]).to_be(FlowResultType.FORM)
    expect(setup_result["step_id"]).to_equal("user")

    with patch.object(
        api,
        "get_devices_by_location",
        AsyncMock(return_value=devices),
    ):
        user_result = await hass.config_entries.flow.async_configure(
            setup_result["flow_id"],
            {"location": {"latitude": 10.0, "longitude": 20.0, "radius": 1.0}},
        )

    expect(user_result["type"]).to_be(FlowResultType.FORM)
    expect(user_result["step_id"]).to_equal("station")

    stations_result = await hass.config_entries.flow.async_configure(
        user_result["flow_id"],
        {
            "station": "AA:AA:AA:AA:AA:AA",
        },
    )

    expect(stations_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(stations_result["title"]).to_equal(config_entry.title)
    expect(stations_result["data"]).to_equal(config_entry.data)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def no_station_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: OpenAPI = Depends(open_api),
    _aioambient: None = Depends(aioambient),
) -> None:
    """Test that we abort when we cannot find a station in the area."""

    setup_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(setup_result["type"]).to_be(FlowResultType.FORM)
    expect(setup_result["step_id"]).to_equal("user")

    with patch.object(
        api,
        "get_devices_by_location",
        AsyncMock(return_value=[]),
    ):
        user_result = await hass.config_entries.flow.async_configure(
            setup_result["flow_id"],
            {"location": {"latitude": 10.0, "longitude": 20.0, "radius": 1.0}},
        )

    expect(user_result["type"]).to_be(FlowResultType.FORM)
    expect(user_result["step_id"]).to_equal("user")
    expect(user_result["errors"]).to_equal({"base": "no_stations_found"})
