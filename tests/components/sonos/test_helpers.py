"""Test the sonos config flow. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def uid_to_hostname() -> None:
    """Stub for test_uid_to_hostname (port deferred)."""
