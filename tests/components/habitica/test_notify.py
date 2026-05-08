"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_platform() -> None:
    """Stub for test_notify_platform."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_message() -> None:
    """Stub for test_send_message."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_message_exceptions() -> None:
    """Stub for test_send_message_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_stale_entities() -> None:
    """Stub for test_remove_stale_entities."""

