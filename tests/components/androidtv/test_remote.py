"""Tryke skip stub for test_remote.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def services_remote() -> None:
    """Stub for test_services_remote."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def services_remote_custom() -> None:
    """Stub for test_services_remote_custom."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_unicode_decode_error() -> None:
    """Stub for test_remote_unicode_decode_error."""

