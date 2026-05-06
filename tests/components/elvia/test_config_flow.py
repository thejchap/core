"""Tryke skip-stubs for elvia config flow tests.

Original tests use recorder_mock fixture; full port deferred.
"""

from tryke import test

@test.skip("recorder_mock fixture")
async def single_metering_point() -> None:
    """Stub for test_single_metering_point (port deferred)."""

@test.skip("recorder_mock fixture")
async def multiple_metering_points() -> None:
    """Stub for test_multiple_metering_points (port deferred)."""

@test.skip("recorder_mock fixture")
async def no_metering_points() -> None:
    """Stub for test_no_metering_points (port deferred)."""

@test.skip("recorder_mock fixture")
async def bad_data() -> None:
    """Stub for test_bad_data (port deferred)."""

@test.skip("recorder_mock fixture")
async def abort_when_metering_point_id_exist() -> None:
    """Stub for test_abort_when_metering_point_id_exist (port deferred)."""

@test.skip("recorder_mock fixture")
async def form_exceptions() -> None:
    """Stub for test_form_exceptions (port deferred)."""
