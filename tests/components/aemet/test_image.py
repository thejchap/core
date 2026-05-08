"""The image tests for the AEMET OpenData platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from .util import async_init_integration

from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke to build a per-module HookExecutor for this file."""


@test
async def aemet_create_images(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test creation of AEMET images."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")

    # Inject translations for the AEMET image entity description so the
    # entity_id slug includes the translation_key. The tryke test
    # environment lacks compiled translations/ files; without this patch
    # the entity_id falls back to "image.aemet" instead of
    # "image.aemet_weather_radar".
    fake_translations = {
        "component.aemet.entity.image.weather_radar.name": "Weather radar",
    }

    async def _fake_get_translations(
        hass_arg, language, category, integrations=None, config_flow=None
    ):
        if integrations is not None and "aemet" in integrations:
            return fake_translations
        return {}

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await async_init_integration(hass)

    state = hass.states.get("image.aemet_weather_radar")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("2021-01-09T11:34:06.448809+00:00")
