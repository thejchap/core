"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def valid_data() -> None:
    """Stub for test_valid_data (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def low_battery() -> None:
    """Stub for test_low_battery (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def initial_states() -> None:
    """Stub for test_initial_states (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def update_states() -> None:
    """Stub for test_update_states (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def unavailable_state() -> None:
    """Stub for test_unavailable_state (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def state_problem_if_unavailable() -> None:
    """Stub for test_state_problem_if_unavailable (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def load_from_db() -> None:
    """Stub for test_load_from_db (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def brightness_history() -> None:
    """Stub for test_brightness_history (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def daily_history_no_data() -> None:
    """Stub for test_daily_history_no_data (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def daily_history_one_day() -> None:
    """Stub for test_daily_history_one_day (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def daily_history_multiple_days() -> None:
    """Stub for test_daily_history_multiple_days (port deferred)."""
