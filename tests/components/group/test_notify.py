"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_message_with_data() -> None:
    """Stub for test_send_message_with_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_configuration() -> None:
    """Stub for test_invalid_configuration."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_notify() -> None:
    """Stub for test_reload_notify."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_entity_group() -> None:
    """Stub for test_notify_entity_group."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting() -> None:
    """Stub for test_state_reporting."""

