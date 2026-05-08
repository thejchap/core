"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def basic_setup() -> None:
    """Stub for test_basic_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def auth_fails() -> None:
    """Stub for test_auth_fails."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def http_info_request_fails() -> None:
    """Stub for test_http_info_request_fails."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def http_favorites_request_fails() -> None:
    """Stub for test_http_favorites_request_fails."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def http_schedule_api_missing() -> None:
    """Stub for test_http_schedule_api_missing."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def events_changed() -> None:
    """Stub for test_events_changed."""

