"""Tryke fixtures for the Prosegur integration."""

from unittest.mock import AsyncMock

from tryke import fixture


@fixture
def mock_list_contracts() -> AsyncMock:
    """Return list of contracts per user."""
    return [
        {"contractId": "123", "description": "a b c"},
        {"contractId": "456", "description": "x y z"},
    ]
