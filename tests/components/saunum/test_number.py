"""Test the Saunum number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("snapshot test — out of scope")
async def set_sauna_duration() -> None:
    """Stub for test_set_sauna_duration (port deferred)."""

@test.skip("snapshot test — out of scope")
async def set_fan_duration() -> None:
    """Stub for test_set_fan_duration (port deferred)."""

@test.skip("snapshot test — out of scope")
async def set_value_failure() -> None:
    """Stub for test_set_value_failure (port deferred)."""

@test.skip("snapshot test — out of scope")
async def set_value_while_session_active() -> None:
    """Stub for test_set_value_while_session_active (port deferred)."""

@test.skip("snapshot test — out of scope")
async def number_with_default_duration() -> None:
    """Stub for test_number_with_default_duration (port deferred)."""

@test.skip("snapshot test — out of scope")
async def number_with_valid_duration_from_device() -> None:
    """Stub for test_number_with_valid_duration_from_device (port deferred)."""
