"""Tryke skip stub for test_image.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def image_platform() -> None:
    """Stub for test_image_platform."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_image_from_url() -> None:
    """Stub for test_load_image_from_url."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_image_not_found() -> None:
    """Stub for test_load_image_not_found."""

