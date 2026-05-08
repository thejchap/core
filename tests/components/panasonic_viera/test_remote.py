"""Tryke skip-stubs for panasonic_viera remote tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def remote_placeholder() -> None:
    """Placeholder skipped sibling tests for test_remote.py."""
