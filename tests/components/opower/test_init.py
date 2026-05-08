"""Tryke skip-stubs for opower init tests.

Original tests use opower API mocks + recorder + statistics; full port deferred.
"""

from tryke import test

@test.skip("opower API mocks + recorder + statistics")
async def setup_unload_entry() -> None:
    """Test successful setup and unload of a config entry."""

@test.skip("opower API mocks + recorder + statistics")
async def login_error() -> None:
    """Test for login error."""

@test.skip("opower API mocks + recorder + statistics")
async def get_forecast_error() -> None:
    """Test for API error when getting forecast."""

@test.skip("opower API mocks + recorder + statistics")
async def get_accounts_error() -> None:
    """Test for API error when getting accounts."""

@test.skip("opower API mocks + recorder + statistics")
async def get_cost_reads_error() -> None:
    """Test for API error when getting cost reads."""
