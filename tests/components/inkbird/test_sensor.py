"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("pending tryke port")
async def device_with_corrupt_name() -> None:
    """Stub for test_device_with_corrupt_name (port deferred)."""

@test.skip("pending tryke port")
async def polling_sensor() -> None:
    """Stub for test_polling_sensor (port deferred)."""

@test.skip("pending tryke port")
async def notify_sensor_no_advertisement() -> None:
    """Stub for test_notify_sensor_no_advertisement (port deferred)."""

@test.skip("pending tryke port")
async def notify_sensor() -> None:
    """Stub for test_notify_sensor (port deferred)."""

@test.skip("pending tryke port")
async def ibs_p02b_sensors() -> None:
    """Stub for test_ibs_p02b_sensors (port deferred)."""
