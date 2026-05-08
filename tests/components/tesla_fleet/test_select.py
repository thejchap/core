"""Tryke skip-stubs for tesla_fleet/test_select.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def select() -> None:
    """Stub for test_select."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def select_offline() -> None:
    """Stub for test_select_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def select_services() -> None:
    """Stub for test_select_services."""

