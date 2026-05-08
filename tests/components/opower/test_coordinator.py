"""Tryke skip-stubs for opower coordinator tests.

Original tests use opower API mocks + recorder + statistics; full port deferred.
"""

from tryke import test

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_first_run() -> None:
    """Test the coordinator on its first run with no existing statistics."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_subsequent_run() -> None:
    """Test the coordinator correctly updates statistics on subsequent runs."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_subsequent_run_no_energy_data() -> None:
    """Test the coordinator handles no recent usage/cost data."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_migration() -> None:
    """Test the one-time migration for return-to-grid statistics."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_api_exceptions() -> None:
    """Test the coordinator handles API exceptions during data fetching."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_updates_with_finer_grained_data() -> None:
    """Test that coarse data is updated when finer-grained data becomes available."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_migration_empty_source_stats() -> None:
    """Test migration logic when source statistics are unexpectedly missing."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_migration_negative_state() -> None:
    """Test that negative consumption states are correctly migrated to return-to-grid statistics."""

@test.skip("opower API mocks + recorder + statistics")
async def coordinator_no_new_cost_reads_after_initial_load() -> None:
    """Test that the coordinator correctly identifies when no new data is available."""
