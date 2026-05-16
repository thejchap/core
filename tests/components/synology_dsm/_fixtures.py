"""Tryke fixtures for the Synology DSM integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from awesomeversion import AwesomeVersion
from synology_dsm.api.file_station.models import SynoFileFile, SynoFileSharedFolder
from synology_dsm.api.photos import SynoPhotosAlbum, SynoPhotosItem
from tryke import Depends, fixture

from homeassistant.components.backup import DOMAIN as BACKUP_DOMAIN
from homeassistant.components.synology_dsm.const import (
    CONF_BACKUP_PATH,
    CONF_BACKUP_SHARE,
    DOMAIN,
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
from homeassistant.setup import async_setup_component
from homeassistant.util.aiohttp import MockStreamReader, MockStreamReaderChunked

from .consts import HOST, MACS, PASSWORD, PORT, USE_SSL, USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

BASE_FILENAME = "Automatic_backup_2025.2.0.dev0_2025-01-09_20.14_35457323"


async def _mock_download_file(path: str, filename: str) -> MockStreamReader:
    """Mock download_file - normal case."""
    if filename == f"{BASE_FILENAME}_meta.json":
        return MockStreamReader(
            b'{"addons":[],"backup_id":"abcd12ef","date":"2025-01-09T20:14:35.457323+01:00",'
            b'"database_included":true,"extra_metadata":{"instance_id":"36b3b7e984da43fc89f7bafb2645fa36",'
            b'"with_automatic_settings":true},"folders":[],"homeassistant_included":true,'
            b'"homeassistant_version":"2025.2.0.dev0","name":"Automatic backup 2025.2.0.dev0","protected":true,"size":13916160}'
        )
    if filename == f"{BASE_FILENAME}.tar":
        return MockStreamReaderChunked(b"backup data")
    raise MockStreamReaderChunked(b"")


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
def mock_dsm_with_filestation() -> Generator[MagicMock]:
    """Mock a successful service with filestation support."""
    with patch("homeassistant.components.synology_dsm.common.SynologyDSM") as dsm:
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
        dsm.file = AsyncMock(
            get_shared_folders=AsyncMock(
                return_value=[
                    SynoFileSharedFolder(
                        additional=None,
                        is_dir=True,
                        name="HA Backup",
                        path="/ha_backup",
                    )
                ]
            ),
            get_files=AsyncMock(
                return_value=[
                    SynoFileFile(
                        additional=None,
                        is_dir=False,
                        name=f"{BASE_FILENAME}_meta.json",
                        path=f"/ha_backup/my_backup_path/{BASE_FILENAME}_meta.json",
                    ),
                    SynoFileFile(
                        additional=None,
                        is_dir=False,
                        name=f"{BASE_FILENAME}.tar",
                        path=f"/ha_backup/my_backup_path/{BASE_FILENAME}.tar",
                    ),
                ]
            ),
            download_file=_mock_download_file,
            upload_file=AsyncMock(return_value=True),
            delete_file=AsyncMock(return_value=True),
        )
        dsm.logout = AsyncMock(return_value=True)
        yield dsm


@fixture
def mock_dsm_without_filestation() -> Generator[MagicMock]:
    """Mock a successful service without filestation support."""
    with patch("homeassistant.components.synology_dsm.common.SynologyDSM") as dsm:
        dsm.login = AsyncMock(return_value=True)
        dsm.update = AsyncMock(return_value=True)

        dsm.surveillance_station.update = AsyncMock(return_value=True)
        dsm.upgrade.update = AsyncMock(return_value=True)
        dsm.utilisation = Mock(cpu_user_load=1, update=AsyncMock(return_value=True))
        dsm.network = Mock(update=AsyncMock(return_value=True), macs=MACS)
        dsm.information = _mock_dsm_information()
        dsm.storage = Mock(
            disks_ids=["sda", "sdb", "sdc"],
            volumes_ids=["volume_1"],
            update=AsyncMock(return_value=True),
        )
        dsm.file = None

        yield dsm


@fixture
async def setup_dsm_with_filestation(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_dsm_with_filestation: MagicMock = Depends(mock_dsm_with_filestation),
) -> AsyncGenerator[MagicMock]:
    """Mock setup of synology dsm config entry."""
    with (
        patch(
            "homeassistant.components.synology_dsm.common.SynologyDSM",
            return_value=mock_dsm_with_filestation,
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
            options={
                CONF_BACKUP_PATH: "my_backup_path",
                CONF_BACKUP_SHARE: "/ha_backup",
            },
            unique_id="mocked_syno_dsm_entry",
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        assert await async_setup_component(hass, BACKUP_DOMAIN, {BACKUP_DOMAIN: {}})
        await hass.async_block_till_done()

        yield mock_dsm_with_filestation


async def _mock_download_file_meta_ok_tar_missing(
    path: str, filename: str
) -> MockStreamReader:
    """Mock download_file - meta ok, tar missing."""
    from synology_dsm.exceptions import SynologyDSMAPIErrorException  # noqa: PLC0415

    if filename == f"{BASE_FILENAME}_meta.json":
        return MockStreamReader(
            b'{"addons":[],"backup_id":"abcd12ef","date":"2025-01-09T20:14:35.457323+01:00",'
            b'"database_included":true,"extra_metadata":{"instance_id":"36b3b7e984da43fc89f7bafb2645fa36",'
            b'"with_automatic_settings":true},"folders":[],"homeassistant_included":true,'
            b'"homeassistant_version":"2025.2.0.dev0","name":"Automatic backup 2025.2.0.dev0","protected":true,"size":13916160}'
        )
    if filename == f"{BASE_FILENAME}.tar":
        raise SynologyDSMAPIErrorException("api", "900", [{"code": 408}])
    raise MockStreamReaderChunked(b"")


async def _mock_download_file_meta_defect(
    path: str, filename: str
) -> MockStreamReader:
    """Mock download_file - meta defect."""
    if filename == f"{BASE_FILENAME}_meta.json":
        return MockStreamReader(b"im not a json")
    if filename == f"{BASE_FILENAME}.tar":
        return MockStreamReaderChunked(b"backup data")
    raise MockStreamReaderChunked(b"")


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
