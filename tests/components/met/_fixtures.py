"""Tryke fixtures for the Met.no integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def met_setup() -> Generator[None]:
    """Patch met setup entry."""
    with patch("homeassistant.components.met.async_setup_entry", return_value=True):
        yield
