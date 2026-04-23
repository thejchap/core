"""Tryke fixtures for Met Éireann config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture


@fixture
def met_eireann_setup() -> Generator[None]:
    """Patch Met Éireann setup entry."""
    with patch(
        "homeassistant.components.met_eireann.async_setup_entry", return_value=True
    ):
        yield
