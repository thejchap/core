"""Tryke skip-stubs for tesla_fleet/test_number.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def number() -> None:
    """Stub for test_number."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def number_offline() -> None:
    """Stub for test_number_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def number_services() -> None:
    """Stub for test_number_services."""

