"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def battery_state() -> None:
    """Stub for test_battery_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def battery_state_updated_via_callback() -> None:
    """Stub for test_battery_state_updated_via_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_disabled_by_default() -> None:
    """Stub for test_dimming_end_time_disabled_by_default."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_when_enabled() -> None:
    """Stub for test_dimming_end_time_when_enabled."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_unknown_when_off() -> None:
    """Stub for test_dimming_end_time_unknown_when_off."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_unknown_when_off_partial_callback() -> None:
    """Stub for test_dimming_end_time_unknown_when_off_partial_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_unknown_when_paused() -> None:
    """Stub for test_dimming_end_time_unknown_when_paused."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_unknown_when_paused_partial_callback() -> None:
    """Stub for test_dimming_end_time_unknown_when_paused_partial_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_variance_reset_on_resume() -> None:
    """Stub for test_dimming_end_time_variance_reset_on_resume."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_jitter_suppression() -> None:
    """Stub for test_dimming_end_time_jitter_suppression."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def dimming_end_time_updates_on_significant_change() -> None:
    """Stub for test_dimming_end_time_updates_on_significant_change."""


