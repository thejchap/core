"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sending_message() -> None:
    """Stub for test_sending_message."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def calling_notify_from_script_loaded_from_yaml() -> None:
    """Stub for test_calling_notify_from_script_loaded_from_yaml."""

