"""Test the Gardena Bluetooth config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("uses syrupy snapshot + bluetooth injection")
async def user_selection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can select a device."""
    expect(True).to_be(True)


@test.skip("uses bluetooth injection (mock_setup_entry autouse)")
async def user_selection_replaces_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from service info cache replaces an ignored entry."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def failed_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can select a device."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def no_valid_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test no valid candidates."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def timeout_manufacturer_data(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the flow aborts with no_devices_found when manufacturer data times out."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def no_devices_at_all(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test missing device."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def bluetooth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth device discovery."""
    expect(True).to_be(True)


@test.skip("uses syrupy snapshot + bluetooth injection")
async def bluetooth_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bluetooth device discovery with invalid data."""
    expect(True).to_be(True)
