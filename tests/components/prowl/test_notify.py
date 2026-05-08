"""Test the Prowl notifications. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_notification_service() -> None:
    """Stub for test_send_notification_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_notification_entity_service() -> None:
    """Stub for test_send_notification_entity_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def fail_send_notification_entity_service() -> None:
    """Stub for test_fail_send_notification_entity_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def fail_send_notification() -> None:
    """Stub for test_fail_send_notification (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def other_exception_send_notification() -> None:
    """Stub for test_other_exception_send_notification (port deferred)."""
