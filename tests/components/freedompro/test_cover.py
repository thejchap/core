"""Tryke skip stub for test_cover.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_get_state() -> None:
    """Stub for test_cover_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_set_position() -> None:
    """Stub for test_cover_set_position."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_close() -> None:
    """Stub for test_cover_close."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cover_open() -> None:
    """Stub for test_cover_open."""

