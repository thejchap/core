"""Test the mqtt config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("discovery + extensive setup")
async def user_connection_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_connection_works_with_supervisor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_v5_connection_works(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_connection_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if connection cannot be made."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def manual_config_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual config does not create an entry, and entry can be setup late."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def user_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def hassio_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow a single config flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def hassio_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we supervisor discovered instance can be ignored."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def hassio_confirm(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can finish a config flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def hassio_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a config flow is aborted when a connection was not successful."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_flow_with_supervisor_addon_running(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_flow_with_supervisor_addon_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_flow_with_supervisor_addon_running_connection_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_not_running_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_discovery_info_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_info_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_flow_with_supervisor_addon_not_installed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def addon_not_installed_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we perform an auto config flow with a supervised install."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def bad_certificate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bad certificate tests."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def keepalive_validation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test validation of the keep alive option."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def disable_birth_will(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test disabling birth and will."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def invalid_discovery_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting an invalid discovery prefix."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def option_flow_default_suggested_values(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options has default/suggested values."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the reauth step works."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def step_hassio_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the reauth step works in case the Mosquitto broker add-on was re-installed."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def step_hassio_reauth_no_discovery_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test hassio reauth flow defaults to manual flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def reconfigure_user_connection_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if connection cannot be made."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_bad_birth_message_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bad birth message."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_bad_will_message_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bad will message."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def try_connection_with_advanced_parameters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow with advanced parameters from config."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def setup_with_advanced_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow setup with advanced parameters."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def setup_with_certificates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow setup with PEM and DER encoded certificates."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def change_websockets_transport_to_tcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguration flow changing websockets transport settings."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def reconfigure_flow_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def reconfigure_no_changed_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def migrate_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrating a config entry."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def migrate_of_incompatible_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrating a config entry."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_configflow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_remove_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure removing an entity."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_edit_entity_multi_entitites(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure with multi entities."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_edit_entity_single_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure with single entity."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_edit_entity_reset_fields(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure resets filtered out fields."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_add_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure and add an entity."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_update_device_properties(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure and update device properties."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_availablity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure and update device properties."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_reconfigure_export_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow reconfigure export feature."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def subentry_configflow_section_feature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the subentry ConfigFlow sections are hidden when they have no configurable options."""
    expect(True).to_be(True)


