"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_entities() -> None:
    """Stub for test_switch_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_toggles() -> None:
    """Stub for test_switch_toggles."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def turbo_mode_not_supported() -> None:
    """Stub for test_turbo_mode_not_supported."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_api_error() -> None:
    """Stub for test_switch_api_error."""


