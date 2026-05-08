"""Tryke skip stub for test_ai_task.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def generate_data() -> None:
    """Stub for test_generate_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def generate_image() -> None:
    """Stub for test_generate_image."""

