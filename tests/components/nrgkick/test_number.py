"""Tryke skip-stubs for nrgkick test_number (port deferred)."""
from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.nrgkick.number module imports cleanly."""
    from homeassistant.components.nrgkick import number  # noqa: PLC0415
    expect(number).not_.to_be(None)


@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def number_entities() -> None:
    """Stub for test_number_entities (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def set_charging_current() -> None:
    """Stub for test_set_charging_current (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def set_energy_limit() -> None:
    """Stub for test_set_energy_limit (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def set_phase_count() -> None:
    """Stub for test_set_phase_count (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def phase_count_filters_transient_zero_on_poll() -> None:
    """Stub for test_phase_count_filters_transient_zero_on_poll (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def phase_count_filters_transient_zero_on_service_call() -> None:
    """Stub for test_phase_count_filters_transient_zero_on_service_call (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def number_command_rejected_by_device() -> None:
    """Stub for test_number_command_rejected_by_device (port deferred)."""

@test.skip("requires snapshot_platform + entity_registry_enabled_by_default (not ported)")
async def charging_current_max_limited_by_connector() -> None:
    """Stub for test_charging_current_max_limited_by_connector (port deferred)."""


