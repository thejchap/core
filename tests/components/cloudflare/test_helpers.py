"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_zone_id() -> None:
    """Stub for test_get_zone_id."""

