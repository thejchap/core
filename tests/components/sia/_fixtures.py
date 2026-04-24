"""Tryke fixtures for SIA tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def mock_sia() -> Generator[None]:
    """Mock SIAClient."""
    with patch("homeassistant.components.sia.hub.SIAClient", autospec=True):
        yield
