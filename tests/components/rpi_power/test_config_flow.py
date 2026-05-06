"""Tests for rpi_power config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.rpi_power.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import patch
from tests.hass_fixtures import hass as hass_fixture, mock_network

MODULE = "homeassistant.components.rpi_power.config_flow.new_under_voltage"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up manually."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(bool(result["errors"])).to_be(False)

    with patch(MODULE, return_value=MagicMock()):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up on not supported system."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(MODULE, return_value=None):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via onboarding."""
    with patch(MODULE, return_value=MagicMock()):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "onboarding"},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def onboarding_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up via onboarding with unsupported system."""
    with patch(MODULE, return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "onboarding"},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
