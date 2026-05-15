"""Tryke skip stub (pending port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import media_source
from homeassistant.components.ai_task.media_source import async_get_media_source
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import init_components, mock_ai_task_entity, mock_config_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def local_media_source(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_components: None = Depends(init_components),
) -> None:
    """Test that the image media source is created."""
    item = await media_source.async_browse_media(hass, "media-source://")

    expect(
        any(c.title == "AI generated images" for c in item.children)
    ).to_be(True)

    source = await async_get_media_source(hass)
    expect(isinstance(source, media_source.local_source.LocalSource)).to_be(True)
    expect(source.name).to_equal("AI generated images")
    expect(source.domain).to_equal("ai_task")
    expect(list(source.media_dirs)).to_equal(["image"])
    # Depending on Docker, the default is one of the two paths
    expect(
        source.media_dirs["image"]
        in ("/media/ai_task/image", hass.config.path("media/ai_task/image"))
    ).to_be(True)
    expect(source.url_prefix).to_equal("/ai_task")

    hass.config.media_dirs = {}

    async with expect_raises_async(
        HomeAssistantError,
        match="AI Task media source requires at least one media directory configured",
    ):
        await async_get_media_source(hass)


_ = (init_components, mock_ai_task_entity, mock_config_entry)
