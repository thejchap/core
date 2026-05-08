"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fronius.sensor module imports cleanly."""
    from homeassistant.components.fronius import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def symo_inverter() -> None:
    """Stub for test_symo_inverter."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def symo_logger() -> None:
    """Stub for test_symo_logger."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def symo_meter() -> None:
    """Stub for test_symo_meter."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def symo_meter_forged() -> None:
    """Stub for test_symo_meter_forged."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def symo_power_flow() -> None:
    """Stub for test_symo_power_flow."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gen24() -> None:
    """Stub for test_gen24."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gen24_storage() -> None:
    """Stub for test_gen24_storage."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def primo_s0() -> None:
    """Stub for test_primo_s0."""

