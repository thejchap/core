"""Tryke skip-stubs for test_api.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_network_settings_active() -> None:
    """Stub for test_async_get_network_settings_active."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_network_settings_inactive() -> None:
    """Stub for test_async_get_network_settings_inactive."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_network_settings_missing() -> None:
    """Stub for test_async_get_network_settings_missing."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_network_settings_failure() -> None:
    """Stub for test_async_get_network_settings_failure."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_radio_type_active() -> None:
    """Stub for test_async_get_radio_type_active."""


@test.skip("zha: sibling test pending tryke port")
async def async_get_radio_path_active() -> None:
    """Stub for test_async_get_radio_path_active."""


@test.skip("zha: sibling test pending tryke port")
async def change_channel() -> None:
    """Stub for test_change_channel."""


@test.skip("zha: sibling test pending tryke port")
async def change_channel_auto() -> None:
    """Stub for test_change_channel_auto."""
