"""Test Suez_water integration initialization. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.suez_water module imports cleanly."""
    from homeassistant.components import suez_water  # noqa: PLC0415
    expect(suez_water).not_.to_be(None)


@test.skip("syrupy snapshot; recorder_mock not in shim")
async def initialization_setup_api_error() -> None:
    """Stub for test_initialization_setup_api_error (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def init_auth_failed() -> None:
    """Stub for test_init_auth_failed (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def init_refresh_failed() -> None:
    """Stub for test_init_refresh_failed (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def init_statistics_failed() -> None:
    """Stub for test_init_statistics_failed (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def statistics_no_price() -> None:
    """Stub for test_statistics_no_price (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def statistics() -> None:
    """Stub for test_statistics (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def migration_version_rollback() -> None:
    """Stub for test_migration_version_rollback (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def no_migration_current_version() -> None:
    """Stub for test_no_migration_current_version (port deferred)."""

@test.skip("syrupy snapshot; recorder_mock not in shim")
async def migration_version_1_to_2() -> None:
    """Stub for test_migration_version_1_to_2 (port deferred)."""
