"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def commands() -> None:
    """Stub for test_commands (port deferred)."""

@test.skip("pending tryke port")
async def non_commands() -> None:
    """Stub for test_non_commands (port deferred)."""

@test.skip("pending tryke port")
async def commands_parsing() -> None:
    """Stub for test_commands_parsing (port deferred)."""
