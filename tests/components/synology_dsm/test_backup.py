"""Tests for the Synology DSM backup agent."""

from io import StringIO
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch

from freezegun.api import FrozenDateTimeFactory
from synology_dsm.exceptions import (
    SynologyDSMAPIErrorException,
    SynologyDSMRequestException,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import (
    DOMAIN as BACKUP_DOMAIN,
    AddonInfo,
    AgentBackup,
    Folder,
)
from homeassistant.components.synology_dsm.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import (
    BASE_FILENAME,
    _mock_download_file_meta_defect,
    _mock_download_file_meta_ok_tar_missing,
    mock_dsm_with_filestation as mock_dsm_with_filestation_fx,
    mock_dsm_without_filestation as mock_dsm_without_filestation_fx,
    setup_dsm_with_filestation as setup_dsm_with_filestation_fx,
)

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    freezer as freezer_fx,
    hass as hass_fx,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Module-level anchor fixture."""
    return 0


@test
async def agents_info(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _setup: MagicMock = Depends(setup_dsm_with_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test backup agent info."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "synology_dsm.mocked_syno_dsm_entry", "name": "Mock Title"},
                {"agent_id": "backup.local", "name": "local"},
            ],
        }
    )


@test
async def agents_not_loaded(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test backup agent with no loaded config entry."""
    with patch("homeassistant.components.backup.is_hassio", return_value=False):
        assert await async_setup_component(hass, BACKUP_DOMAIN, {BACKUP_DOMAIN: {}})
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()
        client = await hass_ws_client(hass)

        await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "backup.local", "name": "local"},
            ],
        }
    )


@test
async def agents_on_unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _setup: MagicMock = Depends(setup_dsm_with_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test backup agent on un-loading config entry."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "synology_dsm.mocked_syno_dsm_entry", "name": "Mock Title"},
                {"agent_id": "backup.local", "name": "local"},
            ],
        }
    )

    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    await hass.config_entries.async_unload(entries[0].entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "backup.local", "name": "local"},
            ],
        }
    )


@test
async def agents_on_changed_update_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test backup agent on changed update success of coordintaor."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()
    expect(len(response["result"]["agents"])).to_equal(2)

    freezer.tick(910)
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()
    expect(len(response["result"]["agents"])).to_equal(2)

    setup_dsm_with_filestation.update.side_effect = SynologyDSMRequestException(
        OSError()
    )
    freezer.tick(910)
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()
    expect(len(response["result"]["agents"])).to_equal(1)

    setup_dsm_with_filestation.update.side_effect = None
    freezer.tick(910)
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()
    expect(len(response["result"]["agents"])).to_equal(2)


@test
async def agents_list_backups(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    _setup: MagicMock = Depends(setup_dsm_with_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent list backups."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal(
        [
            {
                "addons": [],
                "agents": {
                    "synology_dsm.mocked_syno_dsm_entry": {
                        "protected": True,
                        "size": 13916160,
                    }
                },
                "backup_id": "abcd12ef",
                "database_included": True,
                "date": "2025-01-09T20:14:35.457323+01:00",
                "extra_metadata": {
                    "instance_id": ANY,
                    "with_automatic_settings": True,
                },
                "failed_addons": [],
                "failed_agent_ids": [],
                "failed_folders": [],
                "folders": [],
                "homeassistant_included": True,
                "homeassistant_version": "2025.2.0.dev0",
                "name": "Automatic backup 2025.2.0.dev0",
                "with_automatic_settings": None,
            }
        ]
    )


@test
async def agents_list_backups_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent error while list backups."""
    client = await hass_ws_client(hass)

    setup_dsm_with_filestation.file.get_files.side_effect = (
        SynologyDSMAPIErrorException("api", "500", "error")
    )

    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agent_errors": {
                "synology_dsm.mocked_syno_dsm_entry": "Failed to list backups"
            },
            "backups": [],
            "last_attempted_automatic_backup": None,
            "last_completed_automatic_backup": None,
            "last_action_event": None,
            "next_automatic_backup": None,
            "next_automatic_backup_additional": False,
            "state": "idle",
        }
    )


@test
async def agents_list_backups_disabled_filestation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_dsm_without_filestation: MagicMock = Depends(mock_dsm_without_filestation_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent error while list backups when file station is disabled."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(not response["success"]).to_be_truthy()


_BACKUP_DETAILS = {
    "addons": [],
    "agents": {
        "synology_dsm.mocked_syno_dsm_entry": {
            "protected": True,
            "size": 13916160,
        }
    },
    "backup_id": "abcd12ef",
    "database_included": True,
    "date": "2025-01-09T20:14:35.457323+01:00",
    "extra_metadata": {"instance_id": ANY, "with_automatic_settings": True},
    "failed_addons": [],
    "failed_agent_ids": [],
    "failed_folders": [],
    "folders": [],
    "homeassistant_included": True,
    "homeassistant_version": "2025.2.0.dev0",
    "name": "Automatic backup 2025.2.0.dev0",
    "with_automatic_settings": None,
}


@test.cases(
    test.case("found", backup_id="abcd12ef", expected_found=True),
    test.case("not_found", backup_id="12345", expected_found=False),
)
async def agents_get_backup(
    backup_id: str,
    expected_found: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _setup: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent get backup."""
    expected_result: dict[str, Any] | None = _BACKUP_DETAILS if expected_found else None
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backup"]).to_equal(expected_result)


@test
async def agents_get_backup_not_existing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent get not existing backup."""
    client = await hass_ws_client(hass)
    backup_id = "ef34ab12"

    setup_dsm_with_filestation.file.download_file = AsyncMock(
        side_effect=SynologyDSMAPIErrorException("api", "404", "not found")
    )

    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}, "backup": None})


@test
async def agents_get_backup_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent error while get backup."""
    client = await hass_ws_client(hass)
    backup_id = "ef34ab12"

    setup_dsm_with_filestation.file.get_files.side_effect = (
        SynologyDSMAPIErrorException("api", "500", "error")
    )

    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agent_errors": {
                "synology_dsm.mocked_syno_dsm_entry": "Failed to list backups"
            },
            "backup": None,
        }
    )


@test
async def agents_get_backup_defect_meta(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent error while get backup."""
    client = await hass_ws_client(hass)
    backup_id = "ef34ab12"

    setup_dsm_with_filestation.file.download_file = _mock_download_file_meta_defect

    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}, "backup": None})


@test
async def agents_download(
    _trigger: int = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    _setup: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent download backup."""
    client = await hass_client()
    backup_id = "abcd12ef"

    resp = await client.get(
        f"/api/backup/download/{backup_id}?agent_id=synology_dsm.mocked_syno_dsm_entry"
    )
    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")


@test
async def agents_download_not_existing(
    _trigger: int = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent download not existing backup."""
    client = await hass_client()
    backup_id = "abcd12ef"

    setup_dsm_with_filestation.file.download_file = (
        _mock_download_file_meta_ok_tar_missing
    )

    resp = await client.get(
        f"/api/backup/download/{backup_id}?agent_id=synology_dsm.mocked_syno_dsm_entry"
    )
    expect(resp.reason).to_equal("Internal Server Error")
    expect(resp.status).to_equal(500)


@test
async def agents_upload(
    _trigger: int = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent upload backup."""
    client = await hass_client()
    backup_id = "test-backup"
    test_backup = AgentBackup(
        addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
        backup_id=backup_id,
        database_included=True,
        date="1970-01-01T00:00:00.000Z",
        extra_metadata={},
        folders=[Folder.MEDIA, Folder.SHARE],
        homeassistant_included=True,
        homeassistant_version="2024.12.0",
        name="Test",
        protected=True,
        size=0,
    )
    base_filename = "Test_1970-01-01_00.00_00000000"

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
        ) as fetch_backup,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        fetch_backup.return_value = test_backup
        resp = await client.post(
            "/api/backup/upload?agent_id=synology_dsm.mocked_syno_dsm_entry",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(f"Uploading backup {backup_id}" in caplog.text).to_be_truthy()
    mock: AsyncMock = setup_dsm_with_filestation.file.upload_file
    expect(len(mock.mock_calls)).to_equal(2)
    expect(mock.call_args_list[0].kwargs["filename"]).to_equal(f"{base_filename}.tar")
    expect(mock.call_args_list[0].kwargs["path"]).to_equal("/ha_backup/my_backup_path")
    expect(mock.call_args_list[1].kwargs["filename"]).to_equal(
        f"{base_filename}_meta.json"
    )
    expect(mock.call_args_list[1].kwargs["path"]).to_equal("/ha_backup/my_backup_path")


@test
async def agents_upload_error(
    _trigger: int = Depends(_trigger_executor),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent error while uploading backup."""
    client = await hass_client()
    backup_id = "test-backup"
    test_backup = AgentBackup(
        addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
        backup_id=backup_id,
        database_included=True,
        date="1970-01-01T00:00:00.000Z",
        extra_metadata={},
        folders=[Folder.MEDIA, Folder.SHARE],
        homeassistant_included=True,
        homeassistant_version="2024.12.0",
        name="Test",
        protected=True,
        size=0,
    )
    base_filename = "Test_1970-01-01_00.00_00000000"

    # fail to upload the tar file
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
        ) as fetch_backup,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        fetch_backup.return_value = test_backup
        setup_dsm_with_filestation.file.upload_file.side_effect = (
            SynologyDSMAPIErrorException("api", "500", "error")
        )
        resp = await client.post(
            "/api/backup/upload?agent_id=synology_dsm.mocked_syno_dsm_entry",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(f"Uploading backup {backup_id}" in caplog.text).to_be_truthy()
    expect("Failed to upload backup" in caplog.text).to_be_truthy()
    mock: AsyncMock = setup_dsm_with_filestation.file.upload_file
    expect(len(mock.mock_calls)).to_equal(1)
    expect(mock.call_args_list[0].kwargs["filename"]).to_equal(f"{base_filename}.tar")
    expect(mock.call_args_list[0].kwargs["path"]).to_equal("/ha_backup/my_backup_path")

    # fail to upload the meta json file
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
        ) as fetch_backup,
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        fetch_backup.return_value = test_backup
        setup_dsm_with_filestation.file.upload_file.side_effect = [
            True,
            SynologyDSMAPIErrorException("api", "500", "error"),
        ]

        resp = await client.post(
            "/api/backup/upload?agent_id=synology_dsm.mocked_syno_dsm_entry",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(f"Uploading backup {backup_id}" in caplog.text).to_be_truthy()
    expect("Failed to upload backup" in caplog.text).to_be_truthy()
    mock = setup_dsm_with_filestation.file.upload_file
    expect(len(mock.mock_calls)).to_equal(3)
    expect(mock.call_args_list[1].kwargs["filename"]).to_equal(f"{base_filename}.tar")
    expect(mock.call_args_list[1].kwargs["path"]).to_equal("/ha_backup/my_backup_path")
    expect(mock.call_args_list[2].kwargs["filename"]).to_equal(
        f"{base_filename}_meta.json"
    )
    expect(mock.call_args_list[2].kwargs["path"]).to_equal("/ha_backup/my_backup_path")


@test
async def agents_delete(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test agent delete backup."""
    client = await hass_ws_client(hass)
    backup_id = "abcd12ef"

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})
    mock: AsyncMock = setup_dsm_with_filestation.file.delete_file
    expect(len(mock.mock_calls)).to_equal(2)
    expect(mock.call_args_list[0].kwargs["filename"]).to_equal(f"{BASE_FILENAME}.tar")
    expect(mock.call_args_list[0].kwargs["path"]).to_equal("/ha_backup/my_backup_path")
    expect(mock.call_args_list[1].kwargs["filename"]).to_equal(
        f"{BASE_FILENAME}_meta.json"
    )
    expect(mock.call_args_list[1].kwargs["path"]).to_equal("/ha_backup/my_backup_path")


@test
async def agents_delete_not_existing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test delete not existing backup."""
    client = await hass_ws_client(hass)
    backup_id = "ef34ab12"

    setup_dsm_with_filestation.file.download_file = (
        _mock_download_file_meta_ok_tar_missing
    )
    setup_dsm_with_filestation.file.delete_file = AsyncMock(
        side_effect=SynologyDSMAPIErrorException(
            "api",
            "900",
            [{"code": 408, "path": f"/ha_backup/my_backup_path/{backup_id}.tar"}],
        )
    )

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})


@test.cases(
    test.case(
        "code_100",
        error_code="100",
        error_details="Unknown error",
        expected_log="{'api': 'api', 'code': '100', 'reason': 'Unknown', 'details': 'Unknown error'}",
    ),
    test.case(
        "code_900_407",
        error_code="900",
        error_details=[{"code": 407}],
        expected_log="{'api': 'api', 'code': '900', 'reason': 'Unknown', 'details': [{'code': 407}]",
    ),
    test.case(
        "code_900_417",
        error_code="900",
        error_details=[{"code": 417}],
        expected_log="{'api': 'api', 'code': '900', 'reason': 'Unknown', 'details': [{'code': 417}]",
    ),
)
async def agents_delete_error(
    error_code: str,
    error_details: Any,
    expected_log: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    setup_dsm_with_filestation: MagicMock = Depends(setup_dsm_with_filestation_fx),
) -> None:
    """Test error while delete backup."""
    error = SynologyDSMAPIErrorException("api", error_code, error_details)
    client = await hass_ws_client(hass)

    backup_id = "abcd12ef"
    setup_dsm_with_filestation.file.delete_file.side_effect = error
    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agent_errors": {
                "synology_dsm.mocked_syno_dsm_entry": "Failed to delete backup"
            }
        }
    )
    expect(f"Failed to delete backup: {expected_log}" in caplog.text).to_be_truthy()
    mock: AsyncMock = setup_dsm_with_filestation.file.delete_file
    expect(len(mock.mock_calls)).to_equal(1)
    expect(mock.call_args_list[0].kwargs["filename"]).to_equal(f"{BASE_FILENAME}.tar")
    expect(mock.call_args_list[0].kwargs["path"]).to_equal("/ha_backup/my_backup_path")
