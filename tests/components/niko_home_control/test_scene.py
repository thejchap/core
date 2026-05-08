"""Tryke skip-stubs for niko_home_control scene tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def scene_placeholder() -> None:
    """Placeholder skipped sibling tests for test_scene.py."""
