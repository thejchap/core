"""Tryke skip stub for test_infrared.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def infrared_setup_works() -> None:
    """Stub for test_infrared_setup_works."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def infrared_not_created_for_non_ir_device() -> None:
    """Stub for test_infrared_not_created_for_non_ir_device."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def infrared_send_command() -> None:
    """Stub for test_infrared_send_command."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def infrared_send_command_error_translates() -> None:
    """Stub for test_infrared_send_command_error_translates."""

