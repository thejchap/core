"""Tryke skip stub for test_button.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def buttons_created() -> None:
    """Stub for test_buttons_created."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def charge_point_buttons() -> None:
    """Stub for test_charge_point_buttons."""


