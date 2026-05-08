"""Tryke skip-stubs for test_remote.py - sibling port deferred (59 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (59 LOC, 0 parametrize)")
async def send_command() -> None:
    """Stub for test_send_command."""

@test.skip("sibling port deferred (59 LOC, 0 parametrize)")
async def send_command_invalid() -> None:
    """Stub for test_send_command_invalid."""
