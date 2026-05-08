"""Tryke skip-stubs for powerwall binary_sensor tests.

Original tests use Powerwall API mocks; full port deferred.
"""

from tryke import test

@test.skip("Powerwall API mocks")
async def sensors() -> None:
    """Test creation of the binary sensors."""

@test.skip("Powerwall API mocks")
async def sensors_with_empty_meters() -> None:
    """Test creation of the binary sensors with empty meters."""
