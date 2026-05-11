"""Tryke skip-stubs for test_init.py - sibling port deferred (244 LOC, 1 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.honeywell module imports cleanly."""
    from homeassistant.components import honeywell  # noqa: PLC0415
    expect(honeywell).not_.to_be(None)


@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def setup_multiple_entry() -> None:
    """Stub for test_setup_multiple_entry."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def setup_multiple_thermostats() -> None:
    """Stub for test_setup_multiple_thermostats."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def setup_multiple_thermostats_with_same_deviceid() -> None:
    """Stub for test_setup_multiple_thermostats_with_same_deviceid."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def away_temps_migration() -> None:
    """Stub for test_away_temps_migration."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def login_error() -> None:
    """Stub for test_login_error."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def connection_error() -> None:
    """Stub for test_connection_error."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def no_devices() -> None:
    """Stub for test_no_devices."""

@test.skip("sibling port deferred (244 LOC, 1 parametrize)")
async def remove_stale_device() -> None:
    """Stub for test_remove_stale_device."""
