"""Tryke skip-stubs for tesla_fleet/test_switch.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def switch() -> None:
    """Stub for test_switch."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def switch_alt() -> None:
    """Stub for test_switch_alt."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def switch_offline() -> None:
    """Stub for test_switch_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def switch_services() -> None:
    """Stub for test_switch_services."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def switch_no_scope() -> None:
    """Stub for test_switch_no_scope."""

