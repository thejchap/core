"""Test the qBittorrent helpers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def seconds_to_hhmmss() -> None:
    """Stub for test_seconds_to_hhmmss (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def format_unix_timestamp() -> None:
    """Stub for test_format_unix_timestamp (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def format_progress() -> None:
    """Stub for test_format_progress (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def format_torrents() -> None:
    """Stub for test_format_torrents (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def format_torrent() -> None:
    """Stub for test_format_torrent (port deferred)."""
