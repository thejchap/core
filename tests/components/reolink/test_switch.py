"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def switch() -> None:
    """Stub for test_switch (port deferred)."""

@test.skip("pending tryke port")
async def host_switch() -> None:
    """Stub for test_host_switch (port deferred)."""

@test.skip("pending tryke port")
async def chime_switch() -> None:
    """Stub for test_chime_switch (port deferred)."""

@test.skip("pending tryke port")
async def rule_switch() -> None:
    """Stub for test_rule_switch (port deferred)."""
