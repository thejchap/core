"""Tryke skip-stubs for nrgkick test_switch (port deferred)."""
from tryke import test

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def switch_entities() -> None:
    """Stub for test_switch_entities (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def charge_switch_service_calls_update_state() -> None:
    """Stub for test_charge_switch_service_calls_update_state (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def charge_switch_rejected_by_device() -> None:
    """Stub for test_charge_switch_rejected_by_device (port deferred)."""


