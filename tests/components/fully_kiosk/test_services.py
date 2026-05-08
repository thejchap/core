"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def services() -> None:
    """Stub for test_services."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_unloaded_entry() -> None:
    """Stub for test_service_unloaded_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_bad_device_id() -> None:
    """Stub for test_service_bad_device_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_called_with_non_fkb_target_devices() -> None:
    """Stub for test_service_called_with_non_fkb_target_devices."""

