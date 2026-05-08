"""Tryke skip stub for test_number.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def number_entities_snapshot() -> None:
    """Stub for test_number_entities_snapshot."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def number_unknown_device_parameters() -> None:
    """Stub for test_number_unknown_device_parameters."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def number_get_value() -> None:
    """Stub for test_number_get_value."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def set_number_value() -> None:
    """Stub for test_set_number_value."""


