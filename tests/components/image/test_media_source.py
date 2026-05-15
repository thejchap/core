"""Test image media source."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import media_source
from homeassistant.core import HomeAssistant

from tests.components.image._fixtures import mock_image_platform, setup_media_source
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def browsing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _media_source: None = Depends(setup_media_source),
    _platform: None = Depends(mock_image_platform),
) -> None:
    """Test browsing image media source."""
    item = await media_source.async_browse_media(hass, "media-source://image")
    expect(item is not None).to_be(True)
    expect(item.title).to_equal("Image")
    expect(len(item.children)).to_equal(1)
    expect(item.children[0].media_content_type).to_equal("image/jpeg")


@test
async def resolving(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _media_source: None = Depends(setup_media_source),
    _platform: None = Depends(mock_image_platform),
) -> None:
    """Test resolving."""
    item = await media_source.async_resolve_media(
        hass, "media-source://image/image.test", None
    )
    expect(item is not None).to_be(True)
    expect(item.url).to_equal("/api/image_proxy_stream/image.test")
    expect(item.mime_type).to_equal("image/jpeg")


@test
async def resolving_non_existing_camera(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _media_source: None = Depends(setup_media_source),
    _platform: None = Depends(mock_image_platform),
) -> None:
    """Test resolving."""
    async with expect_raises_async(
        media_source.Unresolvable,
        match="Could not resolve media item: image.non_existing",
    ):
        await media_source.async_resolve_media(
            hass, "media-source://image/image.non_existing", None
        )
