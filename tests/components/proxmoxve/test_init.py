"""Tests for the Proxmox VE integration initialization. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.proxmoxve module imports cleanly."""
    from homeassistant.components import proxmoxve  # noqa: PLC0415
    expect(proxmoxve).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_import() -> None:
    """Stub for test_config_import (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_exceptions() -> None:
    """Stub for test_setup_exceptions (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_v1_to_v3() -> None:
    """Stub for test_migration_v1_to_v3 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def offline_node() -> None:
    """Stub for test_offline_node (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_v2_to_v3() -> None:
    """Stub for test_migration_v2_to_v3 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_v2_to_v3_without_realm() -> None:
    """Stub for test_migration_v2_to_v3_without_realm (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def new_vm_creates_entity() -> None:
    """Stub for test_new_vm_creates_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def new_container_creates_entity() -> None:
    """Stub for test_new_container_creates_entity (port deferred)."""
