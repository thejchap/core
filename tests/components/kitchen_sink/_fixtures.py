"""Tryke fixtures for the Everything but the Kitchen Sink integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import fixture

from homeassistant.const import Platform


@fixture
def no_platforms() -> Generator[None]:
    """Don't enable any platforms."""
    with patch(
        "homeassistant.components.kitchen_sink.COMPONENTS_WITH_DEMO_PLATFORM",
        [],
    ):
        yield


@fixture
def infrared_only() -> Generator[None]:
    """Enable only the infrared platform."""
    with patch(
        "homeassistant.components.kitchen_sink.COMPONENTS_WITH_DEMO_PLATFORM",
        [Platform.INFRARED],
    ):
        yield
