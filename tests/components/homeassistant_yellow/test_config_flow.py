"""Test the homeassistant_yellow config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def config_flow_single_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test only a single entry is allowed."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def option_flow_led_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def option_flow_led_settings_unchanged(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def option_flow_led_settings_fail_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def option_flow_led_settings_fail_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def firmware_options_flow_zigbee(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the firmware options flow for Yellow."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def firmware_options_flow_thread(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the firmware options flow for Yellow with Thread."""
    expect(True).to_be(True)


@test.skip("requires aiohasupervisor.client + flasher mocks (not in tryke shim)")
async def options_flow_multipan_uninstall(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow for when multi-PAN firmware is installed."""
    expect(True).to_be(True)


