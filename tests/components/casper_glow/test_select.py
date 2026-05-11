"""Tryke skip stub for test_select.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.casper_glow.select module imports cleanly."""
    from homeassistant.components.casper_glow import select  # noqa: PLC0415
    expect(select).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select_state_from_callback() -> None:
    """Stub for test_select_state_from_callback."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select_option() -> None:
    """Stub for test_select_option."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select_option_error() -> None:
    """Stub for test_select_option_error."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select_state_update_via_callback_after_command_failure() -> None:
    """Stub for test_select_state_update_via_callback_after_command_failure."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def select_ignores_remaining_time_updates() -> None:
    """Stub for test_select_ignores_remaining_time_updates."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def restore_state() -> None:
    """Stub for test_restore_state."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def restore_state_ignores_invalid() -> None:
    """Stub for test_restore_state_ignores_invalid."""


