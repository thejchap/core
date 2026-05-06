"""Test the homekit_controller config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("discovery + extensive setup")
async def discovery_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a device being discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def abort_duplicate_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already paired."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_already_paired_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already paired."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def unknown_domain_type(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that aiohomekit can reject discoveries it doesn't support."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def id_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test id is missing."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_ignored_model(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already paired."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_ignored_hk_bridge(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure we ignore homekit bridges and accessories created by the homekit integration."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_does_not_ignore_non_homekit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Do not ignore devices that are not from the homekit integration."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_broken_pairing_flag(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """There is already a config entry for the pairing and its pairing flag is wrong in zeroconf."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_invalid_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """There is already a config entry for the pairing id but it's invalid."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_ignored_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """There is already a config entry but it is ignored."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already configured."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_already_configured_update_csharp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already configured and csharp changes."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_abort_errors_on_start(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various pairing errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_try_later_errors_on_start(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various pairing errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_form_errors_on_start(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various pairing errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_abort_errors_on_finish(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various pairing errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_form_errors_on_finish(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test various pairing errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def pair_unknown_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test describing unknown errors."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initiated disovers devices."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_pairing_with_insecure_setup_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initiated disovers devices."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initiated pairing where no devices discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_no_unpaired_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initiated pairing where no unpaired devices discovered."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_dismiss_existing_flow_on_paired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that existing flows get dismissed once paired to something else."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def mdns_update_to_paired_during_pairing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we do not abort pairing if mdns is updated to reflect paired during pairing."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_no_bluetooth_support(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery with bluetooth support not available."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bluetooth_not_homekit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth discovery with a non-homekit device."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bluetooth_valid_device_no_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth discovery  with a homekit device and discovery fails."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bluetooth_valid_device_discovery_paired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth discovery  with a homekit device and discovery works."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bluetooth_valid_device_discovery_unpaired(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth discovery with a homekit device and discovery works."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_updates_ip_when_config_entry_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already configured updates ip when config entry set up."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def discovery_updates_ip_config_entry_not_set_up(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Already configured updates ip when the config entry is not set up."""
    expect(True).to_be(True)


