"""Tryke skip-stubs for tesla_fleet/test_update.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update() -> None:
    """Stub for test_update."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update_alt() -> None:
    """Stub for test_update_alt."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update_services() -> None:
    """Stub for test_update_services."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update_scheduled_far_future_not_in_progress() -> None:
    """Stub for test_update_scheduled_far_future_not_in_progress."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update_scheduled_soon_in_progress() -> None:
    """Stub for test_update_scheduled_soon_in_progress."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def update_scheduled_no_time_not_in_progress() -> None:
    """Stub for test_update_scheduled_no_time_not_in_progress."""

