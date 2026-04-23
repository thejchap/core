"""Test the Meteo.lt config flow."""

from unittest.mock import AsyncMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.components.meteo_lt.const import CONF_PLACE_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_meteo_lt_api, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _api: AsyncMock = Depends(mock_meteo_lt_api),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user flow shows form and completes successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PLACE_CODE: "vilnius"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Vilnius")
    expect(result["data"]).to_equal({CONF_PLACE_CODE: "vilnius"})
    expect(result["result"].unique_id).to_equal("vilnius")

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry prevention."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PLACE_CODE: "vilnius"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def api_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_meteo_lt_api: AsyncMock = Depends(mock_meteo_lt_api),
) -> None:
    """Test API connection error during place fetching."""
    mock_meteo_lt_api.places = []
    mock_meteo_lt_api.fetch_places.side_effect = aiohttp.ClientError(
        "Connection failed"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def api_timeout_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_meteo_lt_api: AsyncMock = Depends(mock_meteo_lt_api),
) -> None:
    """Test API timeout error during place fetching."""
    mock_meteo_lt_api.places = []
    mock_meteo_lt_api.fetch_places.side_effect = TimeoutError("Request timed out")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def no_places_found(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_meteo_lt_api: AsyncMock = Depends(mock_meteo_lt_api),
) -> None:
    """Test when API returns no places."""
    mock_meteo_lt_api.places = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_places_found")
