"""Tryke skip stub for test_assist_pipeline.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_pipeline_invalid_platform() -> None:
    """Stub for test_migrate_pipeline_invalid_platform."""

