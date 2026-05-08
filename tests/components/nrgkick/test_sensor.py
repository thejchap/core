"""Tryke skip-stubs for nrgkick test_sensor (port deferred)."""
from tryke import test

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def vehicle_connected_since_none_when_standby() -> None:
    """Stub for test_vehicle_connected_since_none_when_standby (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def sensor_entities() -> None:
    """Stub for test_sensor_entities (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def mapped_unknown_values_become_state_unknown() -> None:
    """Stub for test_mapped_unknown_values_become_state_unknown (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def cellular_and_gps_entities_are_gated_by_model_type() -> None:
    """Stub for test_cellular_and_gps_entities_are_gated_by_model_type (port deferred)."""


