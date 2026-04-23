"""Tryke fixtures for Met.no config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def met_setup() -> Generator[None]:
    """Patch met setup entry."""
    with patch("homeassistant.components.met.async_setup_entry", return_value=True):
        yield
