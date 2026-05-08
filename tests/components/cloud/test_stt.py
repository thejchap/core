"""Tryke skip stub for test_stt.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cloud_speech() -> None:
    """Stub for test_cloud_speech."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrating_pipelines() -> None:
    """Stub for test_migrating_pipelines."""

