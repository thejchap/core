"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gios.sensor module imports cleanly."""
    from homeassistant.components.gios import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def availability_api_error() -> None:
    """Stub for test_availability_api_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dont_create_entities_when_data_missing_for_station() -> None:
    """Stub for test_dont_create_entities_when_data_missing_for_station."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def missing_index_data() -> None:
    """Stub for test_missing_index_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration."""

