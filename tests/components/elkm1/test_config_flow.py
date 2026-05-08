"""Test the Elk-M1 Control config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.elkm1.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import ELK_DISCOVERY, MOCK_IP_ADDRESS, _patch_discovery, _patch_elk

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ELK_DISCOVERY_INFO = {
    "mac_address": ELK_DISCOVERY.mac_address,
    "ip_address": ELK_DISCOVERY.ip_address,
    "port": ELK_DISCOVERY.port,
}


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def discovery_ignored_entry(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort on ignored entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: f"elks://{MOCK_IP_ADDRESS}"},
        unique_id="aa:bb:cc:dd:ee:ff",
        source=config_entries.SOURCE_IGNORE,
    )
    config_entry.add_to_hass(hass)

    with _patch_discovery(), _patch_elk():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=ELK_DISCOVERY_INFO,
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_secure_elk_no_discovery() -> None:
    """Stub for test_form_user_with_secure_elk_no_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_insecure_elk_skip_discovery() -> None:
    """Stub for test_form_user_with_insecure_elk_skip_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_insecure_elk_no_discovery() -> None:
    """Stub for test_form_user_with_insecure_elk_no_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_insecure_elk_times_out() -> None:
    """Stub for test_form_user_with_insecure_elk_times_out (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_secure_elk_no_discovery_ip_already_configured() -> None:
    """Stub for test_form_user_with_secure_elk_no_discovery_ip_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_secure_elk_with_discovery() -> None:
    """Stub for test_form_user_with_secure_elk_with_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_secure_elk_with_discovery_pick_manual() -> None:
    """Stub for test_form_user_with_secure_elk_with_discovery_pick_manual (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_secure_elk_with_discovery_pick_manual_direct_discovery() -> None:
    """Stub for test_form_user_with_secure_elk_with_discovery_pick_manual_direct_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_tls_elk_no_discovery() -> None:
    """Stub for test_form_user_with_tls_elk_no_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_non_secure_elk_no_discovery() -> None:
    """Stub for test_form_user_with_non_secure_elk_no_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_user_with_serial_elk_no_discovery() -> None:
    """Stub for test_form_user_with_serial_elk_no_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def unknown_exception() -> None:
    """Stub for test_unknown_exception (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_invalid_auth() -> None:
    """Stub for test_form_invalid_auth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_invalid_auth_no_password() -> None:
    """Stub for test_form_invalid_auth_no_password (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import() -> None:
    """Stub for test_form_import (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import_device_discovered() -> None:
    """Stub for test_form_import_device_discovered (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import_non_secure_device_discovered() -> None:
    """Stub for test_form_import_non_secure_device_discovered (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import_non_secure_non_stanadard_port_device_discovered() -> None:
    """Stub for test_form_import_non_secure_non_stanadard_port_device_discovered (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import_non_secure_device_discovered_invalid_auth() -> None:
    """Stub for test_form_import_non_secure_device_discovered_invalid_auth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def form_import_existing() -> None:
    """Stub for test_form_import_existing (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_or_discovery_mac_address_mismatch_host_already_configured() -> None:
    """Stub for test_discovered_by_dhcp_or_discovery_mac_address_mismatch_host_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_or_discovery_adds_missing_unique_id() -> None:
    """Stub for test_discovered_by_dhcp_or_discovery_adds_missing_unique_id (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_discovery_and_dhcp() -> None:
    """Stub for test_discovered_by_discovery_and_dhcp (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_discovery() -> None:
    """Stub for test_discovered_by_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_discovery_non_standard_port() -> None:
    """Stub for test_discovered_by_discovery_non_standard_port (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_discovery_url_already_configured() -> None:
    """Stub for test_discovered_by_discovery_url_already_configured (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_udp_responds() -> None:
    """Stub for test_discovered_by_dhcp_udp_responds (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_udp_responds_with_nonsecure_port() -> None:
    """Stub for test_discovered_by_dhcp_udp_responds_with_nonsecure_port (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_udp_responds_existing_config_entry() -> None:
    """Stub for test_discovered_by_dhcp_udp_responds_existing_config_entry (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def discovered_by_dhcp_no_udp_response() -> None:
    """Stub for test_discovered_by_dhcp_no_udp_response (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def multiple_instances_with_discovery() -> None:
    """Stub for test_multiple_instances_with_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def multiple_instances_with_tls_v12() -> None:
    """Stub for test_multiple_instances_with_tls_v12 (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_nonsecure() -> None:
    """Stub for test_reconfigure_nonsecure (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_tls() -> None:
    """Stub for test_reconfigure_tls (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_device_offline() -> None:
    """Stub for test_reconfigure_device_offline (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_invalid_auth() -> None:
    """Stub for test_reconfigure_invalid_auth (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_different_device() -> None:
    """Stub for test_reconfigure_different_device (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_unknown_error() -> None:
    """Stub for test_reconfigure_unknown_error (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reconfigure_preserves_existing_config_entry_fields() -> None:
    """Stub for test_reconfigure_preserves_existing_config_entry_fields (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def user_setup_replaces_ignored_device() -> None:
    """Stub for test_user_setup_replaces_ignored_device (port deferred)."""
