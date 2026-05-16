"""Tryke fixtures for the Synology DSM integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from awesomeversion import AwesomeVersion
from synology_dsm.api.photos import SynoPhotosAlbum, SynoPhotosItem
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


def _mock_dsm_information() -> Mock:
    """Mock SynologyDSM information."""
    return Mock(
        serial="mySerial",
        update=AsyncMock(return_value=True),
        awesome_version=AwesomeVersion("7.2.2"),
        model="DS1821+",
        version_string="DSM 7.2.2-72806 Update 3",
        ram=32768,
        temperature=58,
        uptime=123456,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.synology_dsm.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def service() -> Generator[MagicMock]:
    """Mock a successful Synology service."""
    MACS = ["00-11-32-XX-XX-59", "00-11-32-XX-XX-5A"]
    with patch("homeassistant.components.synology_dsm.config_flow.SynologyDSM") as dsm:
        dsm.login = AsyncMock(return_value=True)
        dsm.update = AsyncMock(return_value=True)

        dsm.surveillance_station.update = AsyncMock(return_value=True)
        dsm.upgrade.update = AsyncMock(return_value=True)
        dsm.utilisation = Mock(cpu_user_load=1, update=AsyncMock(return_value=True))
        dsm.network = Mock(update=AsyncMock(return_value=True), macs=MACS)
        dsm.storage = Mock(
            disks_ids=["sda", "sdb", "sdc"],
            volumes_ids=["volume_1"],
            update=AsyncMock(return_value=True),
        )
        dsm.information = _mock_dsm_information()
        dsm.file = AsyncMock(get_shared_folders=AsyncMock(return_value=None))
        yield dsm


@fixture
async def setup_media_source(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up media source."""
    assert await async_setup_component(hass, "media_source", {})


@fixture
def dsm_with_photos() -> MagicMock:
    """Set up SynologyDSM API fixture with photos."""
    dsm = MagicMock()
    dsm.login = AsyncMock(return_value=True)
    dsm.update = AsyncMock(return_value=True)
    dsm.information = _mock_dsm_information()
    dsm.network.update = AsyncMock(return_value=True)
    dsm.surveillance_station.update = AsyncMock(return_value=True)
    dsm.upgrade.update = AsyncMock(return_value=True)

    dsm.photos.get_albums = AsyncMock(
        return_value=[SynoPhotosAlbum(1, "Album 1", 10, "")]
    )
    dsm.photos.get_items_from_album = AsyncMock(
        return_value=[
            SynoPhotosItem(
                10, "", "filename.jpg", 12345, "10_1298753", "sm", False, ""
            ),
            SynoPhotosItem(10, "", "filename.jpg", 12345, "10_1298753", "sm", True, ""),
        ]
    )
    dsm.photos.get_items_from_shared_space = AsyncMock(
        return_value=[
            SynoPhotosItem(10, "", "filename.jpg", 12345, "10_1298753", "sm", True, ""),
        ]
    )
    dsm.photos.get_item_thumbnail_url = AsyncMock(
        return_value="http://my.thumbnail.url"
    )
    dsm.file = AsyncMock(get_shared_folders=AsyncMock(return_value=None))
    return dsm
