"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def climate() -> None:
    """Stub for test_climate."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setting_climate() -> None:
    """Stub for test_setting_climate."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def incorrect_modes() -> None:
    """Stub for test_incorrect_modes."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failed() -> None:
    """Stub for test_update_failed."""

