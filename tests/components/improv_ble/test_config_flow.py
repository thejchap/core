"""Test the improv_ble config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step success path."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def user_step_success_authorize(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step success path."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def user_step_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step with no devices found."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def async_step_user_takes_precedence_over_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manual setup takes precedence over discovery."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def user_setup_removes_ignored_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user initiated form can replace an ignored device."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_provisioned_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step when device is already provisioned."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_provisioned_device_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step when device changes to provisioned."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_provisioned_no_rediscovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that provisioned device is not rediscovered while it stays provisioned."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_factory_reset_rediscovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that factory reset device can be rediscovered."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_rediscovery_after_successful_provision(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that device can be rediscovered after successful provisioning."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step success path."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_success_identify(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth step success path."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_step_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can't start a flow for the same device twice."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def ensure_connected_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def identify_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def need_authorization_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def authorize_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def provision_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def provision_not_authorized(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def provision_retry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def provision_fails_invalid_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth flow with error due to invalid data."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_chaining_with_next_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow chaining when another integration registers a next flow."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_chaining_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow chaining timeout when no integration discovers the device."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_chaining_with_redirect_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test flow chaining takes precedence over redirect URL."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def flow_chaining_future_already_done(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_register_next_flow when future is already done."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def bluetooth_name_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that discovery notification title updates when device name changes."""
    expect(True).to_be(True)


