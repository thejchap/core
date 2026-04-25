"""Test the Home Assistant Cloud config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import load_homeassistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create cloud entry."""
    with (
        patch(
            "homeassistant.components.cloud.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.cloud.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "system"}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Home Assistant Cloud")
        expect(result["data"]).to_equal({})
        await hass.async_block_till_done()

    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def multiple_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test creating multiple cloud entries."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "system"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
