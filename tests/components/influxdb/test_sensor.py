"""Tryke skip-stubs for test_sensor.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def minimal_config() -> None:
    """Stub for test_minimal_config."""

@test.skip("indirect parametrize unsupported")
async def full_config() -> None:
    """Stub for test_full_config."""

@test.skip("indirect parametrize unsupported")
async def config_failure() -> None:
    """Stub for test_config_failure."""

@test.skip("indirect parametrize unsupported")
async def state_matches_query_result() -> None:
    """Stub for test_state_matches_query_result."""

@test.skip("indirect parametrize unsupported")
async def state_matches_first_query_result_for_multiple_return() -> None:
    """Stub for test_state_matches_first_query_result_for_multiple_return."""

@test.skip("indirect parametrize unsupported")
async def state_for_no_results() -> None:
    """Stub for test_state_for_no_results."""

@test.skip("indirect parametrize unsupported")
async def error_querying_influx() -> None:
    """Stub for test_error_querying_influx."""

@test.skip("indirect parametrize unsupported")
async def error_rendering_template() -> None:
    """Stub for test_error_rendering_template."""

@test.skip("indirect parametrize unsupported")
async def connection_error_at_startup() -> None:
    """Stub for test_connection_error_at_startup."""

@test.skip("indirect parametrize unsupported")
async def data_repository_not_found() -> None:
    """Stub for test_data_repository_not_found."""
