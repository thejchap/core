"""Tryke skip stub for test_conversation.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def entity_availability() -> None:
    """Stub for test_entity_availability."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_handle_message() -> None:
    """Stub for test_async_handle_message."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_handle_message_converse_error() -> None:
    """Stub for test_async_handle_message_converse_error."""

