"""Fixtures for advantage_air tryke port."""

from collections.abc import Generator
from unittest.mock import AsyncMock

from tryke import fixture

from . import patch_get, patch_update


@fixture
def mock_get() -> Generator[AsyncMock]:
    """Fixture to patch the Advantage Air async_get method."""
    with patch_get() as mock_get:
        yield mock_get


@fixture
def mock_update() -> Generator[AsyncMock]:
    """Fixture to patch the Advantage Air async_set method."""
    with patch_update() as mock_get:
        yield mock_get
