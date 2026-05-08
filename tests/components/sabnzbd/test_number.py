"""Number tests for the SABnzbd component. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def number_setup() -> None:
    """Stub for test_number_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def number_set() -> None:
    """Stub for test_number_set (port deferred)."""

@test.skip("syrupy snapshot")
async def number_exception() -> None:
    """Stub for test_number_exception (port deferred)."""

@test.skip("syrupy snapshot")
async def number_unavailable() -> None:
    """Stub for test_number_unavailable (port deferred)."""
