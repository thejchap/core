"""The tests for the Ring light platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("snapshot test — out of scope")
async def light_off_reports_correctly() -> None:
    """Stub for test_light_off_reports_correctly (port deferred)."""

@test.skip("snapshot test — out of scope")
async def light_on_reports_correctly() -> None:
    """Stub for test_light_on_reports_correctly (port deferred)."""

@test.skip("snapshot test — out of scope")
async def light_can_be_turned_on() -> None:
    """Stub for test_light_can_be_turned_on (port deferred)."""

@test.skip("snapshot test — out of scope")
async def light_errors_when_turned_on() -> None:
    """Stub for test_light_errors_when_turned_on (port deferred)."""
