"""Test the EnergyZero config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.energyzero.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.energyzero._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect("flow_id" in result).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2.get("title")).to_equal("EnergyZero")
    expect(result2.get("data")).to_equal({})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def single_instance(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when setting up a duplicate entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("single_instance_allowed")
