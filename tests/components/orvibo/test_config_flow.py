"""Tryke skip-stubs for orvibo config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_menu_display() -> None:
    """Stub for test_user_menu_display (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def edit_flow_success() -> None:
    """Stub for test_edit_flow_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def edit_flow_errors() -> None:
    """Stub for test_edit_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_success() -> None:
    """Stub for test_discovery_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_no_devices() -> None:
    """Stub for test_discovery_no_devices (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_flow_success() -> None:
    """Stub for test_import_flow_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_flow_errors() -> None:
    """Stub for test_import_flow_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discover_skips_existing_and_invalid_mac() -> None:
    """Stub for test_discover_skips_existing_and_invalid_mac (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def start_discovery_shows_progress() -> None:
    """Stub for test_start_discovery_shows_progress (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def discovery_flow_task_exception() -> None:
    """Stub for test_discovery_flow_task_exception (port deferred)."""
