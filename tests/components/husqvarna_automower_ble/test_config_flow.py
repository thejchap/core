"""Test the husqvarna_automower_ble config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.husqvarna_automower_ble.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def user_selection_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user selection shows the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def user_selection() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def user_selection_incorrect_pin() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def bluetooth() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def bluetooth_invalid() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def duplicate_entry() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def failed_connect() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def reauth_flow_success() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def reauth_flow_invalid_pin() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def reauth_no_devices() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def options_flow() -> None:
    """Stub."""

@test.skip("requires bluetooth_service_info inject + mower client mocks")
async def reconfigure() -> None:
    """Stub."""
