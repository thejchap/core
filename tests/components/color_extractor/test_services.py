"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def missing_url_and_path() -> None:
    """Stub for test_missing_url_and_path."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def url_success() -> None:
    """Stub for test_url_success."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def url_not_allowed() -> None:
    """Stub for test_url_not_allowed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def url_exception() -> None:
    """Stub for test_url_exception."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def url_error() -> None:
    """Stub for test_url_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def file() -> None:
    """Stub for test_file."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def file_denied_dir() -> None:
    """Stub for test_file_denied_dir."""

