"""Tryke skip-stubs for test_sensor.py - recorder_mock fixture coupling."""

from tryke import test

@test.skip("recorder_mock fixture coupling")
async def setup() -> None:
    """Stub for test_setup."""

@test.skip("recorder_mock fixture coupling")
async def setup_config_entry() -> None:
    """Stub for test_setup_config_entry."""

@test.skip("recorder_mock fixture coupling")
async def setup_multiple_states() -> None:
    """Stub for test_setup_multiple_states."""

@test.skip("recorder_mock fixture coupling")
async def setup_invalid_config() -> None:
    """Stub for test_setup_invalid_config."""

@test.skip("recorder_mock fixture coupling")
async def invalid_date_for_start() -> None:
    """Stub for test_invalid_date_for_start."""

@test.skip("recorder_mock fixture coupling")
async def invalid_date_for_end() -> None:
    """Stub for test_invalid_date_for_end."""

@test.skip("recorder_mock fixture coupling")
async def invalid_entity_in_template() -> None:
    """Stub for test_invalid_entity_in_template."""

@test.skip("recorder_mock fixture coupling")
async def invalid_entity_returning_none_in_template() -> None:
    """Stub for test_invalid_entity_returning_none_in_template."""

@test.skip("recorder_mock fixture coupling")
async def reload() -> None:
    """Stub for test_reload."""

@test.skip("recorder_mock fixture coupling")
async def measure_multiple() -> None:
    """Stub for test_measure_multiple."""

@test.skip("recorder_mock fixture coupling")
async def measure() -> None:
    """Stub for test_measure."""

@test.skip("recorder_mock fixture coupling")
async def async_on_entire_period() -> None:
    """Stub for test_async_on_entire_period."""

@test.skip("recorder_mock fixture coupling")
async def async_off_entire_period() -> None:
    """Stub for test_async_off_entire_period."""

@test.skip("recorder_mock fixture coupling")
async def async_start_from_history_and_switch_to_watching_state_changes_single() -> None:
    """Stub for test_async_start_from_history_and_switch_to_watching_state_changes_single."""

@test.skip("recorder_mock fixture coupling")
async def async_start_from_history_and_switch_to_watching_state_changes_single_expanding_window() -> None:
    """Stub for test_async_start_from_history_and_switch_to_watching_state_changes_single_expanding_window."""

@test.skip("recorder_mock fixture coupling")
async def async_start_from_history_and_switch_to_watching_state_changes_multiple() -> None:
    """Stub for test_async_start_from_history_and_switch_to_watching_state_changes_multiple."""

@test.skip("recorder_mock fixture coupling")
async def start_from_history_then_watch_state_changes_sliding() -> None:
    """Stub for test_start_from_history_then_watch_state_changes_sliding."""

@test.skip("recorder_mock fixture coupling")
async def does_not_work_into_the_future() -> None:
    """Stub for test_does_not_work_into_the_future."""

@test.skip("recorder_mock fixture coupling")
async def reload_before_start_event() -> None:
    """Stub for test_reload_before_start_event."""

@test.skip("recorder_mock fixture coupling")
async def measure_sliding_window() -> None:
    """Stub for test_measure_sliding_window."""

@test.skip("recorder_mock fixture coupling")
async def measure_from_end_going_backwards() -> None:
    """Stub for test_measure_from_end_going_backwards."""

@test.skip("recorder_mock fixture coupling")
async def measure_cet() -> None:
    """Stub for test_measure_cet."""

@test.skip("recorder_mock fixture coupling")
async def state_change_during_window_rollover() -> None:
    """Stub for test_state_change_during_window_rollover."""

@test.skip("recorder_mock fixture coupling")
async def end_time_with_microseconds_zeroed() -> None:
    """Stub for test_end_time_with_microseconds_zeroed."""

@test.skip("recorder_mock fixture coupling")
async def device_classes() -> None:
    """Stub for test_device_classes."""

@test.skip("recorder_mock fixture coupling")
async def history_stats_handles_floored_timestamps() -> None:
    """Stub for test_history_stats_handles_floored_timestamps."""

@test.skip("recorder_mock fixture coupling")
async def unique_id() -> None:
    """Stub for test_unique_id."""

@test.skip("recorder_mock fixture coupling")
async def device_id() -> None:
    """Stub for test_device_id."""

@test.skip("recorder_mock fixture coupling")
async def async_around_min_state_duration() -> None:
    """Stub for test_async_around_min_state_duration."""

@test.skip("recorder_mock fixture coupling")
async def async_around_min_state_duration_sliding_window() -> None:
    """Stub for test_async_around_min_state_duration_sliding_window."""

@test.skip("recorder_mock fixture coupling")
async def measure_multiple_with_min_state_duration() -> None:
    """Stub for test_measure_multiple_with_min_state_duration."""

@test.skip("recorder_mock fixture coupling")
async def open_block_precision_same_second() -> None:
    """Stub for test_open_block_precision_same_second."""
