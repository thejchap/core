"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""

