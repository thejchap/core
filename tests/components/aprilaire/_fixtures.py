"""Tryke fixtures for the Aprilaire integration."""

from unittest.mock import AsyncMock

from pyaprilaire.client import AprilaireClient
from tryke import fixture


@fixture
def client() -> AprilaireClient:
    """Return a mock client."""
    return AsyncMock(AprilaireClient)
