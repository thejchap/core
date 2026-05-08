"""Tryke skip stub for test_cover.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unknown_position() -> None:
    """Stub for test_unknown_position."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def open_cover() -> None:
    """Stub for test_open_cover."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def close_cover() -> None:
    """Stub for test_close_cover."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_position_cover() -> None:
    """Stub for test_set_position_cover."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stop_cover() -> None:
    """Stub for test_stop_cover."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discover_new_device() -> None:
    """Stub for test_discover_new_device."""

