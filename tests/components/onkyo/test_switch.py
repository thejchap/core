"""Tryke skip-stubs for onkyo switch tests.

Original tests use aioonkyo discovery autouse + receiver mocks; full port deferred.
"""

from tryke import test

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def entities() -> None:
    """Test entities."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def state_changes() -> None:
    """Test NotAvailable message clears channel muting state."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def availability() -> None:
    """Test entity availability on disconnect and reconnect."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def actions() -> None:
    """Test actions."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def query_state_task() -> None:
    """Test query state task."""

@test.skip("aioonkyo discovery autouse + receiver mocks")
async def update_entity() -> None:
    """Test manual entity update."""
