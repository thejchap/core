"""Tryke skip stub for test_vacuum.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def supported_features() -> None:
    """Stub for test_supported_features."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def methods() -> None:
    """Stub for test_methods."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unsupported_methods() -> None:
    """Stub for test_unsupported_methods."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def services() -> None:
    """Stub for test_services."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def set_fan_speed() -> None:
    """Stub for test_set_fan_speed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_command() -> None:
    """Stub for test_send_command."""

