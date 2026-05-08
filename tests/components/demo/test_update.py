"""Tryke skip stub for test_update.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_params() -> None:
    """Stub for test_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_with_progress() -> None:
    """Stub for test_update_with_progress."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_with_progress_raising() -> None:
    """Stub for test_update_with_progress_raising."""

