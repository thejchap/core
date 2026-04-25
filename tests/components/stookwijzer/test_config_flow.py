"""Tests for the Stookwijzer config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.stookwijzer.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_stookwijzer

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    stookwijzer: MagicMock = Depends(mock_stookwijzer),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.1}},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Stookwijzer")
    expect(result["data"]).to_equal(
        {
            CONF_LATITUDE: 450000.123456789,
            CONF_LONGITUDE: 200000.123456789,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(stookwijzer.async_transform_coordinates.mock_calls)).to_equal(1)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    stookwijzer: MagicMock = Depends(mock_stookwijzer),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user configuration flow while connection fails."""
    original_return_value = stookwijzer.async_transform_coordinates.return_value
    stookwijzer.async_transform_coordinates.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.1}},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})

    # Ensure we can continue the flow, when it now works
    stookwijzer.async_transform_coordinates.return_value = original_return_value

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.1}},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
