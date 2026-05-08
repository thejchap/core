"""Test Ridwell calendar platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def calendar_event_varied_states_and_types() -> None:
    """Stub for test_calendar_event_varied_states_and_types (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def calendar_event_with_no_pickups() -> None:
    """Stub for test_calendar_event_with_no_pickups (port deferred)."""
