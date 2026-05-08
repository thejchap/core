"""Tryke skip stub for test_valve.py - all tests use indirect parametrize via config_count fixture."""

from tryke import test


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def state() -> None:
    """Stub for test_state."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def attributes() -> None:
    """Stub for test_attributes."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def open_valves() -> None:
    """Stub for test_open_valves."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def close_valves() -> None:
    """Stub for test_close_valves."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def toggle_valves() -> None:
    """Stub for test_toggle_valves."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def stop_valves() -> None:
    """Stub for test_stop_valves."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def set_valve_position() -> None:
    """Stub for test_set_valve_position."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def is_opening_closing() -> None:
    """Stub for test_is_opening_closing."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def assumed_state() -> None:
    """Stub for test_assumed_state."""


@test.skip("indirect parametrize via config_count -> setup_comp - unsupported")
async def nested_group() -> None:
    """Stub for test_nested_group."""
