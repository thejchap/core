"""Tryke skip-stubs for teslemetry/test_services.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def services() -> None:
    """Stub for test_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def service_validation_errors() -> None:
    """Stub for test_service_validation_errors."""

