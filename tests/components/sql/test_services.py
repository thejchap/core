"""Tryke skip-stubs for SQL test_services."""

from tryke import test


@test.skip("requires recorder + service registration — port deferred")
async def query_service_recorder_db() -> None:
    """Stub for test_query_service_recorder_db."""


@test.skip("requires external DB + tmp_path — port deferred")
async def query_service_external_db() -> None:
    """Stub for test_query_service_external_db."""


@test.skip("requires recorder + rollback — port deferred")
async def query_service_rollback_on_error() -> None:
    """Stub for test_query_service_rollback_on_error."""


@test.skip("requires recorder + data conversion — port deferred")
async def query_service_data_conversion() -> None:
    """Stub for test_query_service_data_conversion."""


@test.skip("requires recorder — port deferred")
async def query_service_no_results() -> None:
    """Stub for test_query_service_no_results."""


@test.skip("requires recorder + service validation — port deferred")
async def query_service_invalid_query_not_select() -> None:
    """Stub for test_query_service_invalid_query_not_select."""


@test.skip("requires recorder + sqlalchemy error context — port deferred")
async def query_service_sqlalchemy_error() -> None:
    """Stub for test_query_service_sqlalchemy_error."""


@test.skip("requires recorder + invalid URL — port deferred")
async def query_service_invalid_db_url() -> None:
    """Stub for test_query_service_invalid_db_url."""


@test.skip("requires recorder + performance issue check — port deferred")
async def query_service_performance_issue_validation() -> None:
    """Stub for test_query_service_performance_issue_validation."""
