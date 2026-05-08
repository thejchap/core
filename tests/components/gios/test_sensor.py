"""Tryke skip stub for test_sensor.py."""

from tryke import test


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

