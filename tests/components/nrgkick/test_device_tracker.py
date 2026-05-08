"""Tryke skip-stubs for nrgkick test_device_tracker (port deferred)."""
from tryke import test

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def device_tracker_entities() -> None:
    """Stub for test_device_tracker_entities (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def device_tracker_not_created_without_sim_module() -> None:
    """Stub for test_device_tracker_not_created_without_sim_module (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def device_tracker_no_gps_data() -> None:
    """Stub for test_device_tracker_no_gps_data (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def device_tracker_with_gps_data() -> None:
    """Stub for test_device_tracker_with_gps_data (port deferred)."""


