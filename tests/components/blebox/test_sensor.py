"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def init() -> None:
    """Stub for test_init."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_failure() -> None:
    """Stub for test_update_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airsensor_init() -> None:
    """Stub for test_airsensor_init."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airsensor_update() -> None:
    """Stub for test_airsensor_update."""

