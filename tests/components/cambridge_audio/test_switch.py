"""Tryke skip stub for test_switch.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setting_value() -> None:
    """Stub for test_setting_value."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def equalizer_switch() -> None:
    """Stub for test_equalizer_switch."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def equalizer_switch_without_user_eq() -> None:
    """Stub for test_equalizer_switch_without_user_eq."""


