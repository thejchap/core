"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def entity_state() -> None:
    """Stub for test_entity_state (port deferred)."""

@test.skip("pending tryke port")
async def services() -> None:
    """Stub for test_services (port deferred)."""

@test.skip("pending tryke port")
async def services_errors() -> None:
    """Stub for test_services_errors (port deferred)."""
