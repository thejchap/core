"""Test the SmartTub binary sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def reminders() -> None:
    """Stub for test_reminders (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def error() -> None:
    """Stub for test_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def snooze_reminder() -> None:
    """Stub for test_snooze_reminder (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def reset_reminder() -> None:
    """Stub for test_reset_reminder (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cover_sensor() -> None:
    """Stub for test_cover_sensor (port deferred)."""
