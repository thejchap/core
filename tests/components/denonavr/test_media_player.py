"""Tryke skip stub for test_media_player.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_command() -> None:
    """Stub for test_get_command."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def dynamic_eq() -> None:
    """Stub for test_dynamic_eq."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_audyssey() -> None:
    """Stub for test_update_audyssey."""

