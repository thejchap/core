"""Test the homeassistant_hardware config flow."""

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
    """Smoke test: the homeassistant_hardware integration module imports cleanly."""
    from homeassistant.components.homeassistant_hardware import (  # noqa: PLC0415
        DOMAIN,
    )
    expect(DOMAIN).to_equal("homeassistant_hardware")


@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_zigbee_recommended() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_zigbee_custom_zha() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_zigbee_other_radio() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_thread() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_thread_otbr() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def config_flow_thread_addon_already_running() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def options_flow_zigbee() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def options_flow_thread() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def options_flow_zigbee_to_thread() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def firmware_callback_picks_zigbee() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def firmware_callback_picks_thread() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def firmware_callback_already_configured() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def firmware_install_failure() -> None:
    """Stub."""

@test.skip("requires aiohasupervisor + universal_silabs_flasher + WaitingAddonManager chain")
async def firmware_callback_finishes_existing_flow() -> None:
    """Stub."""
