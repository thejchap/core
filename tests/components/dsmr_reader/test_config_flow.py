"""Tests for the config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.dsmr_reader.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_step(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user step call."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_be(None)

    config_result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(config_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_result["title"]).to_equal("DSMR Reader")

    duplicate_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(duplicate_result["type"]).to_be(FlowResultType.ABORT)
    expect(duplicate_result["reason"]).to_equal("single_instance_allowed")
