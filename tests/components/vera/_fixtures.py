"""Tryke fixtures for Vera tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from .common import ComponentFactory


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.vera.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def vera_component_factory() -> Generator[ComponentFactory]:
    """Return a factory for initializing the vera component."""
    with patch("pyvera.VeraController") as vera_controller_class_mock:
        yield ComponentFactory(vera_controller_class_mock)
