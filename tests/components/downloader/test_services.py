"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def download_invalid_subdir() -> None:
    """Stub for test_download_invalid_subdir."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def download_headers_passed_through() -> None:
    """Stub for test_download_headers_passed_through."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def download_headers_schema() -> None:
    """Stub for test_download_headers_schema."""

