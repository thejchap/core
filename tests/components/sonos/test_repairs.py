"""Test repairs handling for Sonos. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def subscription_repair_issues() -> None:
    """Stub for test_subscription_repair_issues (port deferred)."""
