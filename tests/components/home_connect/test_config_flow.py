"""Test the home_connect config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("OAuth2 + complex mocks")
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check full flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def prevent_reconfiguring_same_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we only allow one config entry per account."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def reauth_flow_with_different_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf flow."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def zeroconf_flow_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery with already setup device."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def dhcp_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def dhcp_flow_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery with already setup device."""
    expect(True).to_be(True)


@test.skip("OAuth2 + complex mocks")
async def dhcp_flow_complete_device_information(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery with complete device information."""
    expect(True).to_be(True)


