"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def options_reload() -> None:
    """Stub for test_options_reload (port deferred)."""

@test.skip("pending tryke port")
async def setup_auth_fail() -> None:
    """Stub for test_setup_auth_fail (port deferred)."""

@test.skip("pending tryke port")
async def setup_fail() -> None:
    """Stub for test_setup_fail (port deferred)."""

@test.skip("pending tryke port")
async def upnp_missing() -> None:
    """Stub for test_upnp_missing (port deferred)."""

@test.skip("pending tryke port")
async def execute_action_while_shutdown() -> None:
    """Stub for test_execute_action_while_shutdown (port deferred)."""
