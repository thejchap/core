"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_entity_service() -> None:
    """Stub for test_notify_entity_service."""

