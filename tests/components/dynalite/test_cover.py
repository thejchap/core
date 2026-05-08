"""Tryke skip stubs for test_cover - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_setup() -> None:
    """Stub for test_cover_setup (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_without_tilt() -> None:
    """Stub for test_cover_without_tilt (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_positions() -> None:
    """Stub for test_cover_positions (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_restore_state() -> None:
    """Stub for test_cover_restore_state (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_restore_state_bad_cache() -> None:
    """Stub for test_cover_restore_state_bad_cache (port deferred)."""


