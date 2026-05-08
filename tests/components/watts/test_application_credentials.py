"""Tryke skip stub for test_application_credentials.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("watts: sibling test pending tryke port — needs: oauth credentials")
async def application_credentials() -> None:
    """Placeholder skipped sibling tests."""
