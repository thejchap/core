"""Tryke skip-stubs for test_media_source.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media() -> None:
    """Stub for test_browse_media."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media_accounts() -> None:
    """Stub for test_browse_media_accounts."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media_exceptions() -> None:
    """Stub for test_browse_media_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media_not_configured_exception() -> None:
    """Stub for test_browse_media_not_configured_exception."""


@test.skip("xbox: sibling test pending tryke port")
async def browse_media_account_not_configured_exception() -> None:
    """Stub for test_browse_media_account_not_configured_exception."""


@test.skip("xbox: sibling test pending tryke port")
async def resolve_media() -> None:
    """Stub for test_resolve_media."""


@test.skip("xbox: sibling test pending tryke port")
async def resolve_media_exceptions() -> None:
    """Stub for test_resolve_media_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def resolve_media_not_found_exceptions() -> None:
    """Stub for test_resolve_media_not_found_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def resolve_media_not_configured() -> None:
    """Stub for test_resolve_media_not_configured."""


@test.skip("xbox: sibling test pending tryke port")
async def resolve_media_account_not_configured() -> None:
    """Stub for test_resolve_media_account_not_configured."""
