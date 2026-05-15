"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def start() -> None:
    """Stub for test_start (port deferred)."""

@test.skip("pending tryke port")
async def start_without_name() -> None:
    """Stub for test_start_without_name (port deferred)."""

@test.skip("pending tryke port")
async def return_to_base() -> None:
    """Stub for test_return_to_base (port deferred)."""

@test.skip("pending tryke port")
async def return_to_base_without_name() -> None:
    """Stub for test_return_to_base_without_name (port deferred)."""

@test.skip("pending tryke port")
async def clean_area() -> None:
    """Stub for test_clean_area (port deferred)."""

@test.skip("pending tryke port")
async def clean_area_no_matching_vacuum() -> None:
    """Stub for test_clean_area_no_matching_vacuum (port deferred)."""

@test.skip("pending tryke port")
async def clean_area_invalid_area() -> None:
    """Stub for test_clean_area_invalid_area (port deferred)."""

@test.skip("pending tryke port")
async def clean_area_service_failure() -> None:
    """Stub for test_clean_area_service_failure (port deferred)."""
