"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def smartmeter() -> None:
    """Stub for test_smartmeter (port deferred)."""

@test.skip("pending tryke port")
async def phases() -> None:
    """Stub for test_phases (port deferred)."""

@test.skip("pending tryke port")
async def settings() -> None:
    """Stub for test_settings (port deferred)."""

@test.skip("pending tryke port")
async def watermeter() -> None:
    """Stub for test_watermeter (port deferred)."""

@test.skip("pending tryke port")
async def no_watermeter() -> None:
    """Stub for test_no_watermeter (port deferred)."""

@test.skip("pending tryke port")
async def smartmeter_disabled_by_default() -> None:
    """Stub for test_smartmeter_disabled_by_default (port deferred)."""
