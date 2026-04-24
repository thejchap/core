"""Tryke fixtures for pushover tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture


@fixture
def mock_pushover() -> Generator[MagicMock]:
    """Mock pushover API."""
    with patch(
        "pushover_complete.PushoverAPI._generic_post", return_value={}
    ) as mock_generic_post:
        yield mock_generic_post


@fixture
def mock_setup_entry() -> Generator[None]:
    """Patch pushover setup entry."""
    with patch(
        "homeassistant.components.pushover.async_setup_entry", return_value=True
    ):
        yield
