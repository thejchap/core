"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_integration_prevented_by_unavailable_client() -> None:
    """Stub for test_setup_integration_prevented_by_unavailable_client."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_integration_client_returns_none() -> None:
    """Stub for test_setup_integration_client_returns_none."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_multiple_systems_zones() -> None:
    """Stub for test_setup_multiple_systems_zones."""

