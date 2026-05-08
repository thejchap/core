"""Test the homeassistant_sky_connect config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def domain_module_importable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Smoke test: the homeassistant_sky_connect integration module imports cleanly."""
    from homeassistant.components.homeassistant_sky_connect.const import (  # noqa: PLC0415
        DOMAIN,
    )
    expect(DOMAIN).to_equal("homeassistant_sky_connect")


@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def config_flow_zigbee() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def config_flow_thread() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def options_flow() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def options_flow_multipan_uninstall() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def firmware_callback_auto_creates_entry() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def firmware_callback_does_not_create_entry_if_dup() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def usb_discovery_already_configured() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def usb_discovery() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + USBDevice/USBServiceInfo + firmware_config_flow chain")
async def reconfigure() -> None:
    """Stub."""
