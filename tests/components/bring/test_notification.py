"""Tryke skip stub for test_notification.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_notification() -> None:
    """Stub for test_send_notification."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_notification_exception() -> None:
    """Stub for test_send_notification_exception."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_notification_service_validation_error() -> None:
    """Stub for test_send_notification_service_validation_error."""

