"""Tryke skip stub for test_browse_media.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the forked_daapd.browse_media module imports cleanly."""
    from homeassistant.components.forked_daapd import browse_media  # noqa: PLC0415
    expect(browse_media).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_media() -> None:
    """Stub for test_async_browse_media."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_media_not_found() -> None:
    """Stub for test_async_browse_media_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_spotify() -> None:
    """Stub for test_async_browse_spotify."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_media_source() -> None:
    """Stub for test_async_browse_media_source."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_image() -> None:
    """Stub for test_async_browse_image."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_browse_image_missing() -> None:
    """Stub for test_async_browse_image_missing."""

