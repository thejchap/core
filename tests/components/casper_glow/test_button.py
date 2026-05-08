"""Tryke skip stub for test_button.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def button_press_calls_device() -> None:
    """Stub for test_button_press_calls_device."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def button_raises_homeassistant_error_on_failure() -> None:
    """Stub for test_button_raises_homeassistant_error_on_failure."""


