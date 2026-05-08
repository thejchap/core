"""The tests for WebOS TV automation triggers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_trigger_device_id() -> None:
    """Stub for test_turn_on_trigger_device_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def turn_on_trigger_entity_id() -> None:
    """Stub for test_turn_on_trigger_entity_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def wrong_trigger_platform_type() -> None:
    """Stub for test_wrong_trigger_platform_type (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def trigger_invalid_entity_id() -> None:
    """Stub for test_trigger_invalid_entity_id (port deferred)."""
