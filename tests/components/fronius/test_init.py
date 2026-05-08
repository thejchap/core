"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def logger_error() -> None:
    """Stub for test_logger_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def inverter_error() -> None:
    """Stub for test_inverter_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def inverter_night_rescan() -> None:
    """Stub for test_inverter_night_rescan."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def inverter_rescan_interruption() -> None:
    """Stub for test_inverter_rescan_interruption."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices."""

