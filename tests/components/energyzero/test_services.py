"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def has_services() -> None:
    """Stub for test_has_services."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service() -> None:
    """Stub for test_service."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_validation() -> None:
    """Stub for test_service_validation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_called_with_unloaded_entry() -> None:
    """Stub for test_service_called_with_unloaded_entry."""

