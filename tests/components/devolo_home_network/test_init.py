"""Tryke skip stub for test_init.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def setup_device_not_found() -> None:
    """Stub for test_setup_device_not_found."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def hass_stop() -> None:
    """Stub for test_hass_stop."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def device() -> None:
    """Stub for test_device."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def platforms() -> None:
    """Stub for test_platforms."""


