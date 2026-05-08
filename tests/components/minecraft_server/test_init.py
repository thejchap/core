"""Tryke skip-stubs for minecraft_server init tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
