"""Tryke fixtures for the light tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.light import Profiles
from homeassistant.core import HomeAssistant

from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_light_profiles() -> Generator[dict]:
    """Mock loading of profiles."""
    data: dict = {}

    def mock_profiles_class(hass: HomeAssistant) -> Profiles:
        profiles = Profiles(hass)
        profiles.data = data
        profiles.async_initialize = AsyncMock()
        return profiles

    with patch(
        "homeassistant.components.light.Profiles",
        side_effect=mock_profiles_class,
    ):
        yield data


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_lights(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple light entities associated with different targets."""
    return await target_entities(hass, "light")
