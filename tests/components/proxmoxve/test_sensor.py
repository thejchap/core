"""Tests for the Proxmox VE sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def storage_missing_used_fraction() -> None:
    """Stub for test_storage_missing_used_fraction (port deferred)."""
