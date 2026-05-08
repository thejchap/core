"""Tests for radio_browser media_source. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def browsing_local() -> None:
    """Stub for test_browsing_local (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def browsing_exceptions() -> None:
    """Stub for test_browsing_exceptions (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def browsing_not_ready() -> None:
    """Stub for test_browsing_not_ready (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def resolve_media_exceptions() -> None:
    """Stub for test_resolve_media_exceptions (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def resolve_media_not_ready() -> None:
    """Stub for test_resolve_media_not_ready (port deferred)."""
