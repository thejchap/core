"""Tryke fixtures for the media_player tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import setup_recorder_mock


@fixture
async def recorder_mock(
    hass: HomeAssistant = Depends(hass_fixture),
):
    """Set up the recorder for tests that need it."""
    return await setup_recorder_mock(hass)


@fixture
def media_player_only() -> Generator[None]:
    """Enable only the media_player platform on the demo integration."""
    from homeassistant.const import Platform  # noqa: PLC0415

    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.MEDIA_PLAYER],
    ):
        yield


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_media_players(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple media player entities associated with different targets."""
    return await target_entities(hass, "media_player")
