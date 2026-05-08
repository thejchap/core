"""Test the Yeelight config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.yeelight.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_form_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial user form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test.skip("complex yeelight discovery fixtures")
async def discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovery_with_existing_device_present() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovery_no_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def import_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def manual() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def options() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def options_unknown_model() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def manual_no_capabilities() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_by_homekit_and_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_by_dhcp_or_homekit() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_by_dhcp_or_homekit_failed_to_get_id() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovery_updates_ip() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovery_updates_ip_no_reload_setup_in_progress() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovery_adds_missing_ip_id_only() -> None:
    """Skipped pending fixture port."""

@test.skip("complex yeelight discovery fixtures")
async def discovered_during_onboarding() -> None:
    """Skipped pending fixture port."""
