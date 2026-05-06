"""Tryke skip-stubs for environment_canada config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def create_entry() -> None:
    """Stub for test_create_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def create_same_entry_twice() -> None:
    """Stub for test_create_same_entry_twice (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def exception_handling() -> None:
    """Stub for test_exception_handling (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def lat_lon_not_specified() -> None:
    """Stub for test_lat_lon_not_specified (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def coordinates_without_station() -> None:
    """Stub for test_coordinates_without_station (port deferred)."""
