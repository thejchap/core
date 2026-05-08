"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the fronius integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.fronius.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("fronius")


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

