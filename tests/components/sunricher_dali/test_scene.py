"""Test the Sunricher DALI scene platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def activate_scenes() -> None:
    """Stub for test_activate_scenes (port deferred)."""

@test.skip("syrupy snapshot")
async def scene_availability() -> None:
    """Stub for test_scene_availability (port deferred)."""
