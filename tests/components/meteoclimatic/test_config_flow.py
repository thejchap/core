"""Tests for the Meteoclimatic config flow."""

from unittest.mock import MagicMock, patch

from meteoclimatic.exceptions import MeteoclimaticError, StationNotFound
from tryke import Depends, expect, fixture, test

from homeassistant.components.meteoclimatic.const import CONF_STATION_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_STATION_CODE,
    TEST_STATION_NAME,
    client,
    mock_setup,
    patch_requests,
)

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _setup: None = Depends(mock_setup),
    _patch: None = Depends(patch_requests),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_STATION_CODE: TEST_STATION_CODE},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(TEST_STATION_CODE)
    expect(result["title"]).to_equal(TEST_STATION_NAME)
    expect(result["data"][CONF_STATION_CODE]).to_equal(TEST_STATION_CODE)


@test
async def not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("not_found")


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unknown")
