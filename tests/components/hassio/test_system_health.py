"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def hassio_system_health() -> None:
    """Stub for test_hassio_system_health (port deferred)."""

@test.skip("pending tryke port")
async def hassio_system_health_with_issues() -> None:
    """Stub for test_hassio_system_health_with_issues (port deferred)."""
