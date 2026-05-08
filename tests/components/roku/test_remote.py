"""The tests for the Roku remote platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unique_id() -> None:
    """Stub for test_unique_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def main_services() -> None:
    """Stub for test_main_services (port deferred)."""
