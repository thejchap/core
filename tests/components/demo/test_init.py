"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setting_up_demo() -> None:
    """Stub for test_setting_up_demo."""

