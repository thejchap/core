"""Tryke skip-stubs for test_select.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def steam_boiler_level() -> None:
    """Stub for test_steam_boiler_level."""

@test.skip("snapshot test — out of scope")
async def steam_boiler_level_none() -> None:
    """Stub for test_steam_boiler_level_none."""

@test.skip("snapshot test — out of scope")
async def pre_brew_infusion_select() -> None:
    """Stub for test_pre_brew_infusion_select."""

@test.skip("snapshot test — out of scope")
async def pre_brew_infusion_select_none() -> None:
    """Stub for test_pre_brew_infusion_select_none."""

@test.skip("snapshot test — out of scope")
async def smart_standby_mode() -> None:
    """Stub for test_smart_standby_mode."""

@test.skip("snapshot test — out of scope")
async def select_errors() -> None:
    """Stub for test_select_errors."""

@test.skip("snapshot test — out of scope")
async def bbw_dose_mode() -> None:
    """Stub for test_bbw_dose_mode."""
