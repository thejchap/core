"""Tests for Renault selects. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def selects() -> None:
    """Stub for test_selects (port deferred)."""

@test.skip("snapshot test — out of scope")
async def select_empty() -> None:
    """Stub for test_select_empty (port deferred)."""

@test.skip("snapshot test — out of scope")
async def select_errors() -> None:
    """Stub for test_select_errors (port deferred)."""

@test.skip("snapshot test — out of scope")
async def select_access_denied() -> None:
    """Stub for test_select_access_denied (port deferred)."""

@test.skip("snapshot test — out of scope")
async def select_not_supported() -> None:
    """Stub for test_select_not_supported (port deferred)."""

@test.skip("snapshot test — out of scope")
async def select_charge_mode() -> None:
    """Stub for test_select_charge_mode (port deferred)."""
