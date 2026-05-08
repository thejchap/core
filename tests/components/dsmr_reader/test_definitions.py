"""Tryke skip stubs for test_definitions - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dsmr_transform() -> None:
    """Stub for test_dsmr_transform (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def tariff_transform() -> None:
    """Stub for test_tariff_transform (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_tariff() -> None:
    """Stub for test_entity_tariff (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_dsmr_transform() -> None:
    """Stub for test_entity_dsmr_transform (port deferred)."""


