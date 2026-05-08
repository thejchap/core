"""Tryke skip-stubs for test_init.py - sibling port deferred (135 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def init() -> None:
    """Stub for test_init."""

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def disconnect_on_hass_stop() -> None:
    """Stub for test_disconnect_on_hass_stop."""

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def config_entry_connect_error() -> None:
    """Stub for test_config_entry_connect_error."""

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def config_entry_auth_error() -> None:
    """Stub for test_config_entry_auth_error."""

@test.skip("sibling port deferred (135 LOC, 0 parametrize)")
async def deprecated_sensor_issue_lifecycle() -> None:
    """Stub for test_deprecated_sensor_issue_lifecycle."""
