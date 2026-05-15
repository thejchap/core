"""The tests for the evohome coordinator."""

from tryke import test


@test.skip("requires evohome conftest fixtures with indirect parametrize (not in tryke shim)")
async def setup_platform() -> None:
    """Stub for test_setup_platform (port deferred)."""
