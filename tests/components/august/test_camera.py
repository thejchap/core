"""Tryke skip stub for test_camera.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell() -> None:
    """Stub for test_create_doorbell."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def doorbell_refresh_content_token_recover() -> None:
    """Stub for test_doorbell_refresh_content_token_recover."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def doorbell_refresh_content_token_fail() -> None:
    """Stub for test_doorbell_refresh_content_token_fail."""

