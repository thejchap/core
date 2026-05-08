"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def has_services() -> None:
    """Stub for test_has_services."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service() -> None:
    """Stub for test_service."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_filters_datetime_range() -> None:
    """Stub for test_service_filters_datetime_range."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_schema_validation() -> None:
    """Stub for test_service_schema_validation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_schema_validation_vat() -> None:
    """Stub for test_service_schema_validation_vat."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_schema_validation_return_vat() -> None:
    """Stub for test_service_schema_validation_return_vat."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_validation_config_entry_not_found() -> None:
    """Stub for test_service_validation_config_entry_not_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_validation_invalid_date() -> None:
    """Stub for test_service_validation_invalid_date."""

