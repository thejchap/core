"""Tryke skip-stubs for the default_config init tests."""

from tryke import test


@test.skip("requires mock_bluetooth/mock_zeroconf/socket_enabled/recorder (not in tryke shim)")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""
