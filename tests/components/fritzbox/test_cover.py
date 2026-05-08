"""Tryke skip stub for test_cover.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fritzbox.cover module imports cleanly."""
    from homeassistant.components.fritzbox import cover  # noqa: PLC0415
    expect(cover).not_.to_be(None)


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

