"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reboot_button_press_success() -> None:
    """Stub for test_reboot_button_press_success."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reboot_button_press_fail() -> None:
    """Stub for test_reboot_button_press_fail."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def reboot_button_press_exceptions() -> None:
    """Stub for test_reboot_button_press_exceptions."""

