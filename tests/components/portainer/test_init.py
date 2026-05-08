"""Test the Portainer initial specific behavior. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup_exceptions() -> None:
    """Stub for test_setup_exceptions (port deferred)."""

@test.skip("syrupy snapshot")
async def migrations() -> None:
    """Stub for test_migrations (port deferred)."""

@test.skip("syrupy snapshot")
async def remove_config_entry_device() -> None:
    """Stub for test_remove_config_entry_device (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v3_to_v5() -> None:
    """Stub for test_migration_v3_to_v5 (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v4_to_v5() -> None:
    """Stub for test_migration_v4_to_v5 (port deferred)."""

@test.skip("syrupy snapshot")
async def migration_v4_to_v5_exceptions() -> None:
    """Stub for test_migration_v4_to_v5_exceptions (port deferred)."""

@test.skip("syrupy snapshot")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""

@test.skip("syrupy snapshot")
async def container_stack_device_links() -> None:
    """Stub for test_container_stack_device_links (port deferred)."""

@test.skip("syrupy snapshot")
async def new_endpoint_callback() -> None:
    """Stub for test_new_endpoint_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def new_container_callback() -> None:
    """Stub for test_new_container_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def swarm_stacks_fetched_by_swarm_id() -> None:
    """Stub for test_swarm_stacks_fetched_by_swarm_id (port deferred)."""

@test.skip("syrupy snapshot")
async def new_stack_callback() -> None:
    """Stub for test_new_stack_callback (port deferred)."""
