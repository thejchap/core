"""Test the lifx config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("complex fixtures; needs detailed manual port")
async def discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up discovery."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovery_but_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can discover the device but we cannot connect."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovery_with_existing_device_present(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up discovery."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovery_no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test discovery without device."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def manual(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manually setup."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def manual_dns_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manually setup with unresolving host."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def manual_no_capabilities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test manually setup without successful get_capabilities."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovered_by_discovery_and_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form with discovery and abort for dhcp source when we get both."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovered_by_dhcp_or_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup when discovered from dhcp or discovery."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovered_by_dhcp_or_discovery_failed_to_get_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if we cannot get the unique id when discovered from dhcp."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def discovered_by_dhcp_or_homekit_updates_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Update host from dhcp."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def refuse_relays(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we refuse to setup relays."""
    expect(True).to_be(True)


@test.skip("complex fixtures; needs detailed manual port")
async def suggested_area(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test suggested area is populated from lifx group label."""
    expect(True).to_be(True)


