"""Test Qbus scene entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("mqtt_mock not in shim")
async def scene() -> None:
    """Stub for test_scene (port deferred)."""
