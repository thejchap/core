"""Test ReCollect Waste diagnostics. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""
