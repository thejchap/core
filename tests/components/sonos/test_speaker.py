"""Tests for common SonosSpeaker behavior. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def fallback_to_polling() -> None:
    """Stub for test_fallback_to_polling (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def subscription_creation_fails() -> None:
    """Stub for test_subscription_creation_fails (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def zgs_event_group_speakers() -> None:
    """Stub for test_zgs_event_group_speakers (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def zgs_avtransport_group_speakers() -> None:
    """Stub for test_zgs_avtransport_group_speakers (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_offline_without_subscription_lock() -> None:
    """Stub for test_async_offline_without_subscription_lock (port deferred)."""
