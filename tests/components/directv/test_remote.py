"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def unique_id() -> None:
    """Stub for test_unique_id (port deferred)."""

@test.skip("pending tryke port")
async def main_services() -> None:
    """Stub for test_main_services (port deferred)."""
