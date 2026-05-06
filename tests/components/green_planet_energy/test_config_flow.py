"""Test the Green Planet Energy config flow."""

from unittest.mock import AsyncMock, MagicMock

from greenplanet_energy_api import (
    GreenPlanetEnergyAPIError,
    GreenPlanetEnergyConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.green_planet_energy.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_api, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(mock_api),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Green Planet Energy")
    expect(result["data"]).to_equal({})


@test.cases(
    test.case(
        "cannot_connect",
        exception=GreenPlanetEnergyConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "invalid_auth",
        exception=GreenPlanetEnergyAPIError("API error"),
        error_base="invalid_auth",
    ),
    test.case("unknown", exception=Exception("Unknown error"), error_base="unknown"),
)
async def form_errors_and_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    api: MagicMock = Depends(mock_api),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test handling errors and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.get_electricity_prices.side_effect = exception

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    api.get_electricity_prices.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: MagicMock = Depends(mock_api),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
