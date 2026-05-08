"""Tryke skip-stubs for nextdns system health tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def system_health_placeholder() -> None:
    """Placeholder skipped sibling tests for test_system_health.py."""
