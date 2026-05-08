"""Tryke skip stub for test_services.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.services module imports cleanly."""
    from homeassistant.components.fully_kiosk import services  # noqa: PLC0415
    expect(services).not_.to_be(None)


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

