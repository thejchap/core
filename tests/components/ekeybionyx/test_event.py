"""Tryke skip stub for test_event.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def event_entity_setup() -> None:
    """Stub for test_event_entity_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def event_types_attribute() -> None:
    """Stub for test_event_types_attribute."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_unload() -> None:
    """Stub for test_config_entry_unload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def webhook_handler_triggers_event() -> None:
    """Stub for test_webhook_handler_triggers_event."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def webhook_handler_rejects_invalid_auth() -> None:
    """Stub for test_webhook_handler_rejects_invalid_auth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def webhook_handler_missing_auth() -> None:
    """Stub for test_webhook_handler_missing_auth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def webhook_handler_invalid_json() -> None:
    """Stub for test_webhook_handler_invalid_json."""

