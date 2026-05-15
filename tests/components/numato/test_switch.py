"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def failing_setups_no_entities() -> None:
    """Stub for test_failing_setups_no_entities (port deferred)."""

@test.skip("pending tryke port")
async def regular_hass_operations() -> None:
    """Stub for test_regular_hass_operations (port deferred)."""

@test.skip("pending tryke port")
async def failing_hass_operations() -> None:
    """Stub for test_failing_hass_operations (port deferred)."""

@test.skip("pending tryke port")
async def switch_setup_without_discovery_info() -> None:
    """Stub for test_switch_setup_without_discovery_info (port deferred)."""
