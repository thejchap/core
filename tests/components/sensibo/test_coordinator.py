"""The test for the sensibo coordinator. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator() -> None:
    """Stub for test_coordinator (port deferred)."""
