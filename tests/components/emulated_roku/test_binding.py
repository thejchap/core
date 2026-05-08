"""Tryke skip stub for test_binding.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def events_fired_properly() -> None:
    """Stub for test_events_fired_properly."""

