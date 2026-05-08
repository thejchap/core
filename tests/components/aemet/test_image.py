"""Tryke skip stub for test_image.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def aemet_create_images() -> None:
    """Stub for test_aemet_create_images."""

