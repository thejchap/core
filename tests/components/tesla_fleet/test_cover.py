"""Tryke skip-stubs for tesla_fleet/test_cover.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def cover() -> None:
    """Stub for test_cover."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def cover_alt() -> None:
    """Stub for test_cover_alt."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def cover_readonly() -> None:
    """Stub for test_cover_readonly."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def cover_offline() -> None:
    """Stub for test_cover_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def cover_services() -> None:
    """Stub for test_cover_services."""

