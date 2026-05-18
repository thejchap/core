"""Tests for Synology DSM Media Source."""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web
from synology_dsm.exceptions import SynologyDSMException
from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import BrowseError, BrowseMedia, MediaClass
from homeassistant.components.media_source import MediaSourceItem, Unresolvable
from homeassistant.components.synology_dsm.const import DOMAIN
from homeassistant.components.synology_dsm.media_source import (
    SynologyDsmMediaView,
    SynologyPhotosMediaSource,
    async_get_media_source,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from ._fixtures import dsm_with_photos as dsm_with_photos_fx, setup_media_source
from .consts import HOST, MACS, PASSWORD, PORT, USE_SSL, USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx, mock_network, tmp_path as tmp_path_fx
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def get_media_source(
    hass: HomeAssistant = Depends(hass_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test the async_get_media_source function and SynologyPhotosMediaSource constructor."""
    source = await async_get_media_source(hass)
    expect(source).to_be_instance_of(SynologyPhotosMediaSource)
    expect(source.domain).to_equal(DOMAIN)


@test.cases(
    test.case("no_album_id", identifier="unique_id", exception_msg="No album id"),
    test.case("no_file_name", identifier="unique_id/1", exception_msg="No file name"),
    test.case(
        "no_file_name_cache_key",
        identifier="unique_id/1/cache_key",
        exception_msg="No file name",
    ),
    test.case(
        "no_file_extension",
        identifier="unique_id/1/cache_key/filename",
        exception_msg="No file extension",
    ),
)
async def resolve_media_bad_identifier(
    identifier: str,
    exception_msg: str,
    hass: HomeAssistant = Depends(hass_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test resolve_media with bad identifiers."""
    source = await async_get_media_source(hass)
    item = MediaSourceItem(hass, DOMAIN, identifier, None)
    async with expect_raises_async(Unresolvable, match=exception_msg):
        await source.async_resolve_media(item)


@test.cases(
    test.case(
        "jpeg",
        identifier="ABC012345/10/27643_876876/filename.jpg",
        url="/synology_dsm/ABC012345/27643_876876/filename.jpg/",
        mime_type="image/jpeg",
    ),
    test.case(
        "png",
        identifier="ABC012345/12/12631_47189/filename.png",
        url="/synology_dsm/ABC012345/12631_47189/filename.png/",
        mime_type="image/png",
    ),
    test.case(
        "png_shared",
        identifier="ABC012345/12/12631_47189/filename.png_shared",
        url="/synology_dsm/ABC012345/12631_47189/filename.png_shared/",
        mime_type="image/png",
    ),
    test.case(
        "png_passphrase",
        identifier="ABC012345/12_dmypass/12631_47189/filename.png",
        url="/synology_dsm/ABC012345/12631_47189/filename.png/dmypass",
        mime_type="image/png",
    ),
)
async def resolve_media_success(
    identifier: str,
    url: str,
    mime_type: str,
    hass: HomeAssistant = Depends(hass_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test successful resolving an item."""
    source = await async_get_media_source(hass)
    item = MediaSourceItem(hass, DOMAIN, identifier, None)
    result = await source.async_resolve_media(item)

    expect(result.url).to_equal(url)
    expect(result.mime_type).to_equal(mime_type)


@test
async def browse_media_unconfigured(
    hass: HomeAssistant = Depends(hass_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media without any devices being configured."""
    source = await async_get_media_source(hass)
    item = MediaSourceItem(
        hass, DOMAIN, "unique_id/album_id/cache_key/filename.jpg", None
    )
    async with expect_raises_async(BrowseError, match="Diskstation not initialized"):
        await source.async_browse_media(item)


async def _setup_entry(
    hass: HomeAssistant, dsm_with_photos: MagicMock
) -> MockConfigEntry:
    """Set up a mock config entry for synology_dsm."""
    with (
        patch(
            "homeassistant.components.synology_dsm.common.SynologyDSM",
            return_value=dsm_with_photos,
        ),
        patch("homeassistant.components.synology_dsm.PLATFORMS", return_value=[]),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
                CONF_MAC: MACS[0],
            },
            unique_id="mocked_syno_dsm_entry",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    return entry


@test
async def browse_media_album_error(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media with unknown album."""
    entry = await _setup_entry(hass, dsm_with_photos)

    dsm_with_photos.photos.get_albums = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )

    source = await async_get_media_source(hass)

    item = MediaSourceItem(hass, DOMAIN, entry.unique_id, None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.identifier).to_be_none()
    expect(result.children).to_have_length(0)


@test
async def browse_media_get_root(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media returning root media sources."""
    await _setup_entry(hass, dsm_with_photos)

    source = await async_get_media_source(hass)
    item = MediaSourceItem(hass, DOMAIN, "", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.children).to_have_length(1)
    expect(result.children[0]).to_be_instance_of(BrowseMedia)
    expect(result.children[0].identifier).to_equal("mocked_syno_dsm_entry")


@test
async def browse_media_get_albums(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media returning albums."""
    await _setup_entry(hass, dsm_with_photos)

    source = await async_get_media_source(hass)
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.children).to_have_length(3)
    expect(result.children[0]).to_be_instance_of(BrowseMedia)
    expect(result.children[0].identifier).to_equal("mocked_syno_dsm_entry/0")
    expect(result.children[0].title).to_equal("All images")
    expect(result.children[1]).to_be_instance_of(BrowseMedia)
    expect(result.children[1].identifier).to_equal("mocked_syno_dsm_entry/shared")
    expect(result.children[1].title).to_equal("Shared space")
    expect(result.children[2]).to_be_instance_of(BrowseMedia)
    expect(result.children[2].identifier).to_equal("mocked_syno_dsm_entry/1_")
    expect(result.children[2].title).to_equal("Album 1")


@test
async def browse_media_get_items_error(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media returning albums."""
    await _setup_entry(hass, dsm_with_photos)

    source = await async_get_media_source(hass)

    # unknown album
    dsm_with_photos.photos.get_items_from_album = AsyncMock(return_value=[])
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.identifier).to_be_none()
    expect(result.children).to_have_length(0)

    # exception in get_items_from_album()
    dsm_with_photos.photos.get_items_from_album = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.identifier).to_be_none()
    expect(result.children).to_have_length(0)

    # exception in get_items_from_shared_space()
    dsm_with_photos.photos.get_items_from_shared_space = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/shared", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.identifier).to_be_none()
    expect(result.children).to_have_length(0)


@test
async def browse_media_get_items_thumbnail_error(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media returning albums."""
    await _setup_entry(hass, dsm_with_photos)

    source = await async_get_media_source(hass)

    dsm_with_photos.photos.get_item_thumbnail_url = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.children).to_have_length(2)
    child = result.children[0]
    expect(child).to_be_instance_of(BrowseMedia)
    expect(child.thumbnail).to_be_none()


@test
async def browse_media_get_items(
    hass: HomeAssistant = Depends(hass_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test browse_media returning albums."""
    await _setup_entry(hass, dsm_with_photos)

    source = await async_get_media_source(hass)

    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/1", None)
    result = await source.async_browse_media(item)

    expect(result).to_be_truthy()
    expect(result.children).to_have_length(2)
    child = result.children[0]
    expect(child).to_be_instance_of(BrowseMedia)
    expect(child.identifier).to_equal(
        "mocked_syno_dsm_entry/1_/10_1298753/filename.jpg"
    )
    expect(child.title).to_equal("filename.jpg")
    expect(child.media_class).to_equal(MediaClass.IMAGE)
    expect(child.media_content_type).to_equal("image/jpeg")
    expect(child.can_play).to_be_truthy()
    expect(child.can_expand).to_be_falsy()
    expect(child.thumbnail).to_equal("http://my.thumbnail.url")
    child = result.children[1]
    expect(child).to_be_instance_of(BrowseMedia)
    expect(child.identifier).to_equal(
        "mocked_syno_dsm_entry/1_/10_1298753/filename.jpg_shared"
    )
    expect(child.title).to_equal("filename.jpg")
    expect(child.media_class).to_equal(MediaClass.IMAGE)
    expect(child.media_content_type).to_equal("image/jpeg")
    expect(child.can_play).to_be_truthy()
    expect(child.can_expand).to_be_falsy()
    expect(child.thumbnail).to_equal("http://my.thumbnail.url")

    item = MediaSourceItem(hass, DOMAIN, "mocked_syno_dsm_entry/shared", None)
    result = await source.async_browse_media(item)
    expect(result).to_be_truthy()
    expect(result.children).to_have_length(1)
    child = result.children[0]
    expect(child.identifier).to_equal(
        "mocked_syno_dsm_entry/shared_/10_1298753/filename.jpg_shared"
    )
    expect(child.title).to_equal("filename.jpg")
    expect(child.media_class).to_equal(MediaClass.IMAGE)
    expect(child.media_content_type).to_equal("image/jpeg")
    expect(child.can_play).to_be_truthy()
    expect(child.can_expand).to_be_falsy()
    expect(child.thumbnail).to_equal("http://my.thumbnail.url")


@test
async def media_view(
    hass: HomeAssistant = Depends(hass_fx),
    tmp_path: Path = Depends(tmp_path_fx),
    dsm_with_photos: MagicMock = Depends(dsm_with_photos_fx),
    _setup: None = Depends(setup_media_source),
) -> None:
    """Test SynologyDsmMediaView returning albums."""
    from homeassistant.util.aiohttp import MockRequest  # noqa: PLC0415

    view = SynologyDsmMediaView(hass)
    request = MockRequest(b"", DOMAIN)

    # diskation not set uped
    async with expect_raises_async(web.HTTPNotFound):
        await view.get(request, "", "")

    await _setup_entry(hass, dsm_with_photos)

    async with expect_raises_async(web.HTTPNotFound):
        await view.get(request, "", "10_1298753/filename/")

    # exception in download_item()
    dsm_with_photos.photos.download_item = AsyncMock(
        side_effect=SynologyDSMException("", None)
    )
    async with expect_raises_async(web.HTTPNotFound):
        await view.get(request, "mocked_syno_dsm_entry", "10_1298753/filename.jpg/")

    # success
    dsm_with_photos.photos.download_item = AsyncMock(return_value=b"xxxx")
    with patch.object(tempfile, "tempdir", tmp_path):
        result = await view.get(
            request, "mocked_syno_dsm_entry", "10_1298753/filename.jpg/"
        )
        expect(result).to_be_instance_of(web.Response)
    with patch.object(tempfile, "tempdir", tmp_path):
        result = await view.get(
            request, "mocked_syno_dsm_entry", "10_1298753/filename.jpg_shared/"
        )
        expect(result).to_be_instance_of(web.Response)
