"""Tryke skip-stubs for nut test_sensor (port deferred)."""
from tryke import test

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def pdu_dynamic_outlets() -> None:
    """Stub for test_pdu_dynamic_outlets (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def ups_devices() -> None:
    """Stub for test_ups_devices (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def ups_devices_with_unique_ids() -> None:
    """Stub for test_ups_devices_with_unique_ids (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def pdu_devices_with_unique_ids() -> None:
    """Stub for test_pdu_devices_with_unique_ids (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def state_sensors() -> None:
    """Stub for test_state_sensors (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def unknown_state_sensors() -> None:
    """Stub for test_unknown_state_sensors (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def stale_options() -> None:
    """Stub for test_stale_options (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def state_ambient_translation() -> None:
    """Stub for test_state_ambient_translation (port deferred)."""

@test.skip("requires syrupy snapshot or complex device_action infra (not ported)")
async def pdu_devices_ambient_not_present() -> None:
    """Stub for test_pdu_devices_ambient_not_present (port deferred)."""


