"""Tryke skip-stubs for SolarEdge coordinator tests."""

from tryke import test


@test.skip("requires recorder + freezer + statistics — port deferred")
async def solaredgeoverviewdataservice_energy_values_validity() -> None:
    """Stub for test_solaredgeoverviewdataservice_energy_values_validity."""


@test.skip("requires recorder + freezer + statistics — port deferred")
async def modules_coordinator_first_run() -> None:
    """Stub for test_modules_coordinator_first_run."""


@test.skip("requires recorder + freezer + statistics — port deferred")
async def modules_coordinator_subsequent_run() -> None:
    """Stub for test_modules_coordinator_subsequent_run."""


@test.skip("requires recorder + freezer + statistics — port deferred")
async def modules_coordinator_subsequent_run_with_gap() -> None:
    """Stub for test_modules_coordinator_subsequent_run_with_gap."""


@test.skip("requires recorder + freezer + statistics + caplog — port deferred")
async def modules_coordinator_no_energy_data() -> None:
    """Stub for test_modules_coordinator_no_energy_data."""
