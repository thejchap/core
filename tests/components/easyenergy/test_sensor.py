"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energy_usage_today() -> None:
    """Stub for test_energy_usage_today."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def energy_return_today() -> None:
    """Stub for test_energy_return_today."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def gas_today() -> None:
    """Stub for test_gas_today."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_gas_today() -> None:
    """Stub for test_no_gas_today."""

