"""Tryke skip stub for test_coordinator.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def coordinator_first_run() -> None:
    """Stub for test_coordinator_first_run."""


@test.skip("snapshot test — out of scope")
async def coordinator_subsequent_run() -> None:
    """Stub for test_coordinator_subsequent_run."""


@test.skip("snapshot test — out of scope")
async def coordinator_subsequent_run_no_energy_data() -> None:
    """Stub for test_coordinator_subsequent_run_no_energy_data."""


@test.skip("snapshot test — out of scope")
async def coordinator_invalid_readings() -> None:
    """Stub for test_coordinator_invalid_readings."""


@test.skip("snapshot test — out of scope")
async def coordinator_subsequent_run_missing_period_statistics() -> None:
    """Stub for test_coordinator_subsequent_run_missing_period_statistics."""


@test.skip("snapshot test — out of scope")
async def coordinator_period_statistics_without_sum() -> None:
    """Stub for test_coordinator_period_statistics_without_sum."""


