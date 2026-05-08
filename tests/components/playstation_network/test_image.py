"""Tryke skip-stubs for playstation_network image tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def image_placeholder() -> None:
    """Placeholder skipped sibling tests for test_image.py."""
