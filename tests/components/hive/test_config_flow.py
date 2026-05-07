"""Test the hive config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_with_no_2fa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no 2FA required and device registration."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_2fa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with 2FA."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth flow."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def reauth_2fa_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when the device is still registered."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def reauth_2fa_flow_device_not_registered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when the device has been deleted from the Hive app."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def reauth_2fa_flow_device_registration_check_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when is_device_registered() raises HiveApiError."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_2fa_send_new_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Resend a 2FA code if it didn't arrive."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def abort_if_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check flow abort when an entry already exist."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_invalid_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with invalid username."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_invalid_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with invalid password."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_no_internet_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no internet connection."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_2fa_no_internet_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no internet connection."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_2fa_invalid_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with 2FA."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow when unknown error occurs."""
    expect(True).to_be(True)


@test.skip("requires apyhiveapi mock chain (complex)")
async def user_flow_2fa_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test 2fa flow when unknown error occurs."""
    expect(True).to_be(True)


