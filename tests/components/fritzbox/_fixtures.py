"""Tryke fixtures for the fritzbox integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture


@fixture
def fritz() -> Generator[Mock]:
    """Patch fritzbox libraries (test_config_flow's local fritz fixture)."""
    with (
        patch("homeassistant.components.fritzbox.async_setup_entry"),
        patch("homeassistant.components.fritzbox.config_flow.Fritzhome") as fritz,
    ):
        yield fritz
