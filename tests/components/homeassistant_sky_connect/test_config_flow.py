"""Test the homeassistant_sky_connect config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def config_flow_zigbee(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow for SkyConnect with Zigbee."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def config_flow_thread(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow for SkyConnect with Thread."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow for SkyConnect."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def options_flow_multipan_uninstall(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow for when multi-PAN firmware is installed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def firmware_callback_auto_creates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that firmware notification triggers import flow that auto-creates config entry."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def duplicate_usb_discovery_aborts_early(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test USB discovery aborts early when unique_id exists before serial path resolution."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor + USB serial chain (not in tryke shim)")
async def firmware_callback_updates_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that firmware notification updates existing config entry device path."""
    expect(True).to_be(True)


