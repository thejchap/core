"""Test the Home Assistant Supervisor config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _do_config_flow(hass: HomeAssistant) -> None:
    """Run the standard hassio config flow and assert success."""
    with (
        patch(
            "homeassistant.components.hassio.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.hassio.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Supervisor")
        expect(result["data"]).to_equal({})
        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    await _do_config_flow(hass)


@test
async def multiple_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating multiple hassio entries."""
    await _do_config_flow(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "system"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
