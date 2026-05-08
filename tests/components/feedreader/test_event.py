"""Tryke skip stub for test_event.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def event_entity() -> None:
    """Stub for test_event_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def event_htmlentities() -> None:
    """Stub for test_event_htmlentities."""

