"""Test ZHA Silicon Labs Multiprotocol support."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.zha import silabs_multiprotocol
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for tryke Depends() resolution."""
    return hass


@test
async def async_get_channel_no_zha(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reading channel with no ZHA config entries and no database."""
    expect(await silabs_multiprotocol.async_get_channel(hass)).to_be(None)


@test
async def async_using_multipan_no_zha(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test async_using_multipan with no ZHA config entries and no database."""
    expect(await silabs_multiprotocol.async_using_multipan(hass)).to_be(False)


@test.skip("requires setup_zha fixture (zigpy_app_controller, etc.)")
async def async_get_channel_active() -> None:
    """Stub for test_async_get_channel_active (port deferred)."""


@test.skip("requires setup_zha fixture (zigpy_app_controller, etc.)")
async def async_get_channel_missing() -> None:
    """Stub for test_async_get_channel_missing (port deferred)."""


@test.skip("requires setup_zha fixture (zigpy_app_controller, etc.)")
async def async_using_multipan_active() -> None:
    """Stub for test_async_using_multipan_active (port deferred)."""


@test.skip("requires setup_zha fixture (zigpy_app_controller, etc.)")
async def change_channel() -> None:
    """Stub for test_change_channel (port deferred)."""


@test.skip("requires zigpy_app_controller fixture")
async def change_channel_no_zha() -> None:
    """Stub for test_change_channel_no_zha (port deferred)."""


@test.skip("requires setup_zha fixture (zigpy_app_controller, etc.)")
async def change_channel_delay() -> None:
    """Stub for test_change_channel_delay (port deferred)."""
