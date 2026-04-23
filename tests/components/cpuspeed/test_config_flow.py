"""Tests for the CPU Speed config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.cpuspeed.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.cpuspeed._fixtures import (
    mock_config_entry,
    mock_cpuinfo_config_flow,
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
    mock_cpuinfo_config_flow: MagicMock = Depends(mock_cpuinfo_config_flow),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result2.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2.get("title")).to_equal("CPU Speed")
    expect(result2.get("data")).to_equal({})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_cpuinfo_config_flow.mock_calls)).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_cpuinfo_config_flow: MagicMock = Depends(mock_cpuinfo_config_flow),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("single_instance_allowed")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(mock_cpuinfo_config_flow.mock_calls)).to_equal(0)


@test
async def not_compatible(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_cpuinfo_config_flow: MagicMock = Depends(mock_cpuinfo_config_flow),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort the configuration flow when incompatible."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")

    mock_cpuinfo_config_flow.return_value = {}
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result2.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result2.get("reason")).to_equal("not_compatible")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(mock_cpuinfo_config_flow.mock_calls)).to_equal(1)
