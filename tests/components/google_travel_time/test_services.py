"""Tryke skip stub for test_services.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_travel_time.services module imports cleanly."""
    from homeassistant.components.google_travel_time import services  # noqa: PLC0415
    expect(services).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_travel_times() -> None:
    """Stub for test_service_get_travel_times."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_travel_times_with_all_options() -> None:
    """Stub for test_service_get_travel_times_with_all_options."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_travel_times_empty_response() -> None:
    """Stub for test_service_get_travel_times_empty_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_travel_times_errors() -> None:
    """Stub for test_service_get_travel_times_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_transit_times() -> None:
    """Stub for test_service_get_transit_times."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_transit_times_with_all_options() -> None:
    """Stub for test_service_get_transit_times_with_all_options."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_get_transit_times_errors() -> None:
    """Stub for test_service_get_transit_times_errors."""

