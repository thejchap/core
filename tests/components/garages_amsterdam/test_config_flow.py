"""Test the Garages Amsterdam config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from aiohttp import ClientResponseError
from tryke import Depends, expect, fixture, test

from homeassistant.components.garages_amsterdam.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_garages_amsterdam, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    garages: AsyncMock = Depends(mock_garages_amsterdam),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(bool(result.get("errors"))).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"garage_name": "IJDok"},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("IJDok")
    expect(result.get("data")).to_equal({"garage_name": "IJDok"})
    expect(len(garages.all_garages.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("runtime_error", side_effect=RuntimeError, reason="unknown"),
    test.case(
        "client_response_error",
        side_effect=ClientResponseError(None, None, status=HTTPStatus.INTERNAL_SERVER_ERROR),
        reason="cannot_connect",
    ),
)
async def error_handling(
    side_effect: Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test error handling in the config flow."""
    with patch(
        "homeassistant.components.garages_amsterdam.config_flow.ODPAmsterdam.all_garages",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(reason)
