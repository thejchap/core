"""Tryke fixtures for the door tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_binary_sensors(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple binary sensor entities associated with different targets."""
    return await target_entities(hass, "binary_sensor")


@fixture
async def target_covers(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple cover entities associated with different targets."""
    return await target_entities(hass, "cover")
