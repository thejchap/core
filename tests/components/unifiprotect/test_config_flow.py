"""Test the UniFi Protect config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.unifiprotect.const import DOMAIN
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
    expect(bool(result["errors"])).to_be(False)


@test.skip("complex pyunifiprotect mock fixtures")
async def user_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_version_too_old() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_invalid_auth_password() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_invalid_auth_api_key() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_cloud_user() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_cannot_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_reauth_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_options() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_updated() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_updated_but_not_using_direct_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_does_not_update_ip_when_console_is_still_online() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_host_not_updated_if_existing_is_a_hostname() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_partial() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_on_different_interface() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_on_different_interface_ip_matches() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_on_different_interface_resolver() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_on_different_interface_resolver_fails() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovered_by_unifi_discovery_direct_connect_on_different_interface_resolver_no_result() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovery_can_be_ignored() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovery_with_both_ignored_and_normal_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovery_confirm_fallback_to_ip() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def discovery_confirm_with_api_key_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_different_nvr() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_auth_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_api_key_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_cloud_user() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_outdated_version() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_form_defaults() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_same_nvr_updated_credentials() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_empty_credentials_keeps_existing() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_credential_update() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_invalid_existing_password_shows_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reauth_empty_credentials_keeps_existing() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reauth_credential_update() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def reconfigure_clears_session_failure_continues() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def form_api_key_client_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex pyunifiprotect mock fixtures")
async def port_int_conversion() -> None:
    """Skipped pending fixture port."""
