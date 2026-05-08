"""Tryke skip-stubs for onkyo init tests.

Original tests use aioonkyo discovery autouse + receiver mocks; full port deferred.
"""

from tryke import test

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def load_unload_entry() -> None:
    """Test load and unload entry."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def initialization_failure() -> None:
    """Test initialization failure."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def connection_failure() -> None:
    """Test connection failure."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def reconnect() -> None:
    """Test reconnect."""
