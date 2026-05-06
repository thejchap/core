"""Tryke skip-stubs for openweathermap config flow tests.

Original tests use pytest indirect parametrize; full port deferred.
"""

from tryke import test

@test.skip("pytest indirect parametrize")
async def successful_config_flow() -> None:
    """Stub for test_successful_config_flow (port deferred)."""

@test.skip("pytest indirect parametrize")
async def abort_config_flow() -> None:
    """Stub for test_abort_config_flow (port deferred)."""

@test.skip("pytest indirect parametrize")
async def config_flow_options_change() -> None:
    """Stub for test_config_flow_options_change (port deferred)."""

@test.skip("pytest indirect parametrize")
async def form_invalid_api_key() -> None:
    """Stub for test_form_invalid_api_key (port deferred)."""

@test.skip("pytest indirect parametrize")
async def form_api_call_error() -> None:
    """Stub for test_form_api_call_error (port deferred)."""
