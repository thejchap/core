"""Tryke skip-stubs for test_cover.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def window_cover() -> None:
    """Stub for test_window_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def fibaro_fgr222_shutter_cover() -> None:
    """Stub for test_fibaro_fgr222_shutter_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def fibaro_fgr223_shutter_cover() -> None:
    """Stub for test_fibaro_fgr223_shutter_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def shelly_wave_shutter_cover_with_tilt() -> None:
    """Stub for test_shelly_wave_shutter_cover_with_tilt."""


@test.skip("zwave_js: sibling test pending tryke port")
async def aeotec_nano_shutter_cover() -> None:
    """Stub for test_aeotec_nano_shutter_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def blind_cover() -> None:
    """Stub for test_blind_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def shutter_cover() -> None:
    """Stub for test_shutter_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def motor_barrier_cover() -> None:
    """Stub for test_motor_barrier_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def motor_barrier_cover_no_primary_value() -> None:
    """Stub for test_motor_barrier_cover_no_primary_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def fibaro_fgr222_shutter_cover_no_tilt() -> None:
    """Stub for test_fibaro_fgr222_shutter_cover_no_tilt."""


@test.skip("zwave_js: sibling test pending tryke port")
async def fibaro_fgr223_shutter_cover_no_tilt() -> None:
    """Stub for test_fibaro_fgr223_shutter_cover_no_tilt."""


@test.skip("zwave_js: sibling test pending tryke port")
async def iblinds_v3_cover() -> None:
    """Stub for test_iblinds_v3_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def nice_ibt4zwave_cover() -> None:
    """Stub for test_nice_ibt4zwave_cover."""


@test.skip("zwave_js: sibling test pending tryke port")
async def window_covering_open_close() -> None:
    """Stub for test_window_covering_open_close."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_working() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_working."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_closing() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_closing."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_success_no_moving() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_success_no_moving."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_unsupervised() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_unsupervised."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_stop_clears() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_stop_clears."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_set_position() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_set_position."""


@test.skip("zwave_js: sibling test pending tryke port")
async def window_covering_cover_moving_state() -> None:
    """Stub for test_window_covering_cover_moving_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_moving_state_none_result() -> None:
    """Stub for test_multilevel_switch_cover_moving_state_none_result."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_v3_no_moving_state_supervised() -> None:
    """Stub for test_multilevel_switch_cover_v3_no_moving_state_supervised."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_cover_v3_no_moving_state_unsupervised() -> None:
    """Stub for test_multilevel_switch_cover_v3_no_moving_state_unsupervised."""


@test.skip("zwave_js: sibling test pending tryke port")
async def window_covering_cover_moving_state_position_support() -> None:
    """Stub for test_window_covering_cover_moving_state_position_support."""


@test.skip("zwave_js: sibling test pending tryke port")
async def window_covering_cover_moving_state_no_position() -> None:
    """Stub for test_window_covering_cover_moving_state_no_position."""
