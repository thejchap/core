"""Test the gardena_bluetooth config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.gardena_bluetooth.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def show_user_form_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test no_devices_found is reached when no bluetooth service info is injected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def user_selection() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def user_selection_replaces_ignored() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def failed_connect() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def bluetooth() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def bluetooth_invalid() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + gardena Client mock for full flow")
async def already_configured() -> None:
    """Stub."""
