"""Tryke skip-stubs for test_update.py - sibling port deferred (140 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (140 LOC, 0 parametrize)")
async def robot_with_no_update() -> None:
    """Stub for test_robot_with_no_update."""

@test.skip("sibling port deferred (140 LOC, 0 parametrize)")
async def robot_with_update() -> None:
    """Stub for test_robot_with_update."""

@test.skip("sibling port deferred (140 LOC, 0 parametrize)")
async def robot_with_update_already_in_progress() -> None:
    """Stub for test_robot_with_update_already_in_progress."""

@test.skip("sibling port deferred (140 LOC, 0 parametrize)")
async def update_command_exception() -> None:
    """Stub for test_update_command_exception."""
