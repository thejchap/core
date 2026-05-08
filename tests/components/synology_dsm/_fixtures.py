"""Tryke fixtures for the Synology DSM integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from awesomeversion import AwesomeVersion
from tryke import fixture


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
