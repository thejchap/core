"""Tryke skip-stubs for tesla_fleet/test_climate.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate() -> None:
    """Stub for test_climate."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_services() -> None:
    """Stub for test_climate_services."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_overheat_protection_services() -> None:
    """Stub for test_climate_overheat_protection_services."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_alt() -> None:
    """Stub for test_climate_alt."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_offline() -> None:
    """Stub for test_climate_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def invalid_error() -> None:
    """Stub for test_invalid_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def errors() -> None:
    """Stub for test_errors."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def ignored_error() -> None:
    """Stub for test_ignored_error."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def asleep_or_offline() -> None:
    """Stub for test_asleep_or_offline."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_noscope() -> None:
    """Stub for test_climate_noscope."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def climate_notemp() -> None:
    """Stub for test_climate_notemp."""

