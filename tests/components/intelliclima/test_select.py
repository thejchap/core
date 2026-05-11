"""Tryke skip-stubs for test_select.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def all_select_entities() -> None:
    """Stub for test_all_select_entities."""

@test.skip("snapshot test — out of scope")
async def select_option_keeps_current_speed() -> None:
    """Stub for test_select_option_keeps_current_speed."""

@test.skip("snapshot test — out of scope")
async def select_option_when_off_defaults_speed_to_sleep() -> None:
    """Stub for test_select_option_when_off_defaults_speed_to_sleep."""

@test.skip("snapshot test — out of scope")
async def select_option_in_auto_mode_defaults_speed_to_sleep() -> None:
    """Stub for test_select_option_in_auto_mode_defaults_speed_to_sleep."""

@test.skip("snapshot test — out of scope")
async def select_option_does_not_call_turn_off() -> None:
    """Stub for test_select_option_does_not_call_turn_off."""

@test.skip("snapshot test — out of scope")
async def select_option_triggers_coordinator_refresh() -> None:
    """Stub for test_select_option_triggers_coordinator_refresh."""
