"""Tryke skip stub for test_repairs.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def change_schedule_fails() -> None:
    """Stub for test_change_schedule_fails."""

