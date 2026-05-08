"""The tests for SleepIQ light platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def light_set_states() -> None:
    """Stub for test_light_set_states (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_get_states() -> None:
    """Stub for test_switch_get_states (port deferred)."""
