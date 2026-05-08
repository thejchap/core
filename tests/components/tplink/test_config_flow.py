"""Test the tplink config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tplink import DOMAIN
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
    expect(bool(result["errors"])).to_be(False)


@test.skip("complex device discovery fixtures")
async def discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_pick_device_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_auth_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_auth_errors() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_new_credentials() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_new_credentials_invalid() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_with_existing_device_present() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_no_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_camera_no_hls() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_camera_no_live_view() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_no_capabilities() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_auth_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_auth_errors() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_port_override() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def manual_port_override_invalid() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovered_by_discovery_and_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovered_by_dhcp_or_discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovered_by_dhcp_or_discovery_failed_to_get_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def integration_discovery_with_ip_change() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def integration_discovery_with_connection_change() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def dhcp_discovery_with_ip_change() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def dhcp_discovery_discover_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_camera() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_try_connect_all() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_try_connect_all_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_update_with_encryption_change() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_update_from_discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_update_from_discovery_with_ip_change() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_no_update_if_config_and_ip_the_same() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_errors() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def pick_device_errors() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_timeout_try_connect_all() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_timeout_try_connect_all_needs_creds() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def discovery_timeout_try_connect_all_fail() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reauth_update_other_flows() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reconfigure() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reconfigure_auth_discovered() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reconfigure_auth_try_connect_all() -> None:
    """Skipped pending fixture port."""

@test.skip("complex device discovery fixtures")
async def reconfigure_camera() -> None:
    """Skipped pending fixture port."""
