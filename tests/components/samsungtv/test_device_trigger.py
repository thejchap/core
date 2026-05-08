"""The tests for Samsung TV device triggers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def get_triggers() -> None:
    """Stub for test_get_triggers (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def if_fires_on_turn_on_request() -> None:
    """Stub for test_if_fires_on_turn_on_request (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios (port deferred)."""
