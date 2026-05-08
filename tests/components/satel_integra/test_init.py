"""Test init of Satel Integra integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def config_flow_migration_v1_1_to_v1_2() -> None:
    """Stub for test_config_flow_migration_v1_1_to_v1_2 (port deferred)."""

@test.skip("syrupy snapshot")
async def config_flow_migration_v1_to_v2() -> None:
    """Stub for test_config_flow_migration_v1_to_v2 (port deferred)."""

@test.skip("syrupy snapshot")
async def config_flow_migration_v2_1_to_v2_2() -> None:
    """Stub for test_config_flow_migration_v2_1_to_v2_2 (port deferred)."""

@test.skip("syrupy snapshot")
async def parent_device_exists() -> None:
    """Stub for test_parent_device_exists (port deferred)."""

@test.skip("syrupy snapshot")
async def setup_exceptions() -> None:
    """Stub for test_setup_exceptions (port deferred)."""
