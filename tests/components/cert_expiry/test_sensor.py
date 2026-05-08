"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry_bad_cert() -> None:
    """Stub for test_async_setup_entry_bad_cert."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_sensor() -> None:
    """Stub for test_update_sensor."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_sensor_network_errors() -> None:
    """Stub for test_update_sensor_network_errors."""

