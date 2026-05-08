"""Tryke skip-stubs for matter adapter tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def adapter_placeholder() -> None:
    """Placeholder skipped sibling tests for test_adapter.py."""
