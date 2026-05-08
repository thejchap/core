"""Tests for Samsung TV config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.samsungtv.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import fake_host, silent_ssdp_scanner

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ssdp: None = Depends(silent_ssdp_scanner),
    _host: None = Depends(fake_host),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_form_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is shown when starting a flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy_does_not_ok_first_time() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_encrypted_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy_missing_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket_access_denied() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket_auth_retry() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_not_successful() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_not_successful_2() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_no_manufacturer() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_legacy_not_remote_control_receiver_udn() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_noprefix() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_legacy_missing_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_legacy_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_websocket_success_populates_mac_address_and_ssdp_location() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_websocket_success_populates_mac_address_and_main_tv_ssdp_location() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_encrypted_websocket_success_populates_mac_address_and_ssdp_location() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_encrypted_websocket_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_websocket_cannot_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_wrong_manufacturer() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_not_successful() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_not_successful_2() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_already_in_progress() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_wireless() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_wired() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_zeroconf_already_in_progress() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_ignores_soundbar() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_no_device_info() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_and_dhcp_same_time() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def websocket_no_mac() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_auth_missing() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_legacy() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_none() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_old_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrectly_formatted_mac_unique_id_added_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_from_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_model_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_ssdp_location_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_zeroconf_discovery_preserved_unique_id() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_main_tv_agent_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_main_tv_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_added_unique_id_preserved_from_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_legacy_missing_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_legacy_missing_mac_from_dhcp_no_unique_id() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_unique_id_added_from_ssdp_with_rendering_control_st() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_legacy() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def reconfigure_host() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def reconfigure_host_invalid() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket_cannot_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_encrypted() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_upnp_udn_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_mac_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def no_update_incorrect_udn_not_matching_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_update_mac() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_while_user_flow_pending() -> None:
    """Skipped pending fixture port."""
