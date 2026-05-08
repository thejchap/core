"""Tryke skip stub for test_event.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_setup() -> None:
    """Stub for test_entity_setup."""

