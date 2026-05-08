"""Tryke skip stub for test_image.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def image_setup() -> None:
    """Stub for test_image_setup."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def guest_wifi_qr() -> None:
    """Stub for test_guest_wifi_qr."""


