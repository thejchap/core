"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def hls_playlist_supported() -> None:
    """Stub for test_hls_playlist_supported."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def parse_playlist() -> None:
    """Stub for test_parse_playlist."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def parse_bad_playlist() -> None:
    """Stub for test_parse_bad_playlist."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def parse_http_error() -> None:
    """Stub for test_parse_http_error."""

