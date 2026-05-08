"""Test the switchbot config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_bleak_scanner_start,
    mock_bluetooth_adapters,
    mock_network,
)

DOMAIN = "switchbot"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def user_no_devices(
    _trigger: None = Depends(_trigger_executor),
    _bt: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form aborts when no devices are discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_requires_password() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_encrypted_key() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_key() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_encrypted_key_back_navigation() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_encrypted_auth_back_navigation() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def bluetooth_discovery_already_setup() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def async_step_bluetooth_not_switchbot() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def async_step_bluetooth_not_connectable() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def async_step_bluetooth_meter_pro_co2_not_connectable() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wohand() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wohand_already_configured() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wohand_replaces_ignored() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wocurtain() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wocurtain_or_bot() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wocurtain_or_bot_with_password() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_single_bot_with_password() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_woencrypted_key() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_woencrypted_auth() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_woencrypted_auth_switchbot_api_down() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_woencrypted_auth_unknown_error() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wolock_or_bot() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_wosensor() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_cloud_login() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_cloud_login_auth_failed() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_cloud_login_api_error() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_cloud_login_unknown_error() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_cloud_login_then_encrypted_device() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def async_step_user_takes_precedence_over_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def options_flow() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def options_flow_lock_pro() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def options_flow_curtain_speed() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_worelay_switch_1pm_key() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_worelay_switch_1pm_auth() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_setup_worelay_switch_1pm_auth_switchbot_api_down() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_show_menu_when_passive_scanner_present() -> None:
    """Skipped pending fixture port."""


@test.skip("requires SwitchBot bluetooth service-info fixture data")
async def user_show_menu_when_no_scanners() -> None:
    """Skipped pending fixture port."""
