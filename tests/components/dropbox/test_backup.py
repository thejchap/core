"""Test the Dropbox backup platform."""

import asyncio
from collections.abc import AsyncIterator
from io import StringIO
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from python_dropbox_api import DropboxAuthException
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import (
    AddonInfo,
    AgentBackup,
    suggested_filename,
)
from homeassistant.components.dropbox.backup import (
    DropboxFileOrFolderNotFoundException,
    DropboxUnknownException,
    async_register_backup_agents_listener,
)
from homeassistant.components.dropbox.const import DATA_BACKUP_AGENT_LISTENERS, DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.core import HomeAssistant

from ._fixtures import (
    CONFIG_ENTRY_TITLE,
    TEST_AGENT_ID,
    mock_config_entry as mock_config_entry_fx,
    setup_integration as setup_integration_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fx,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.test_util.aiohttp import mock_stream


# Required for async tests with Depends.
@fixture
def _trigger_executor() -> int:
    return 0


TEST_AGENT_BACKUP = AgentBackup(
    addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
    backup_id="dropbox-backup",
    database_included=True,
    date="2025-01-01T00:00:00.000Z",
    extra_metadata={"with_automatic_settings": False},
    folders=[],
    homeassistant_included=True,
    homeassistant_version="2024.12.0",
    name="Dropbox backup",
    protected=False,
    size=2048,
)

TEST_AGENT_BACKUP_RESULT = {
    "addons": [{"name": "Test", "slug": "test", "version": "1.0.0"}],
    "agents": {TEST_AGENT_ID: {"protected": False, "size": 2048}},
    "backup_id": TEST_AGENT_BACKUP.backup_id,
    "database_included": True,
    "date": TEST_AGENT_BACKUP.date,
    "extra_metadata": {"with_automatic_settings": False},
    "failed_addons": [],
    "failed_agent_ids": [],
    "failed_folders": [],
    "folders": [],
    "homeassistant_included": True,
    "homeassistant_version": TEST_AGENT_BACKUP.homeassistant_version,
    "name": TEST_AGENT_BACKUP.name,
    "with_automatic_settings": None,
}


def _suggested_filenames(backup: AgentBackup) -> tuple[str, str]:
    """Return the suggested filenames for the backup and metadata."""
    base_name = suggested_filename(backup).rsplit(".", 1)[0]
    return f"{base_name}.tar", f"{base_name}.metadata.json"


async def _mock_metadata_stream(backup: AgentBackup) -> AsyncIterator[bytes]:
    """Create a mock metadata download stream."""
    yield json.dumps(backup.as_dict()).encode()


def _setup_list_folder_with_backup(
    mock_dropbox_client: MagicMock,
    backup: AgentBackup,
) -> None:
    """Set up mock to return a backup in list_folder and download_file."""
    tar_name, metadata_name = _suggested_filenames(backup)
    mock_dropbox_client.list_folder = AsyncMock(
        return_value=[
            SimpleNamespace(name=tar_name),
            SimpleNamespace(name=metadata_name),
        ]
    )
    mock_dropbox_client.download_file = Mock(return_value=_mock_metadata_stream(backup))


@test
async def agents_info(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test listing available backup agents."""
    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "backup.local", "name": "local"},
                {"agent_id": TEST_AGENT_ID, "name": CONFIG_ENTRY_TITLE},
            ]
        }
    )

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {"agents": [{"agent_id": "backup.local", "name": "local"}]}
    )


@test
async def agents_list_backups(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test listing backups via the Dropbox agent."""
    _setup_list_folder_with_backup(mock_dropbox_client, TEST_AGENT_BACKUP)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal([TEST_AGENT_BACKUP_RESULT])
    mock_dropbox_client.list_folder.assert_awaited()


@test
async def agents_list_backups_metadata_without_tar(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test that orphaned metadata files are skipped with a warning."""
    mock_dropbox_client.list_folder = AsyncMock(
        return_value=[SimpleNamespace(name="orphan.metadata.json")]
    )

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal([])
    expect("without matching backup file" in caplog.text).to_be(True)


@test
async def agents_list_backups_invalid_metadata(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test that invalid metadata files are skipped with a warning."""

    async def _invalid_stream() -> AsyncIterator[bytes]:
        yield b"not valid json"

    mock_dropbox_client.list_folder = AsyncMock(
        return_value=[
            SimpleNamespace(name="backup.tar"),
            SimpleNamespace(name="backup.metadata.json"),
        ]
    )
    mock_dropbox_client.download_file = Mock(return_value=_invalid_stream())

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal([])
    expect("Skipping invalid metadata file" in caplog.text).to_be(True)


@test
async def agents_list_backups_fail(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test handling list backups failures."""
    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxUnknownException("boom")
    )

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["backups"]).to_equal([])
    expect(response["result"]["agent_errors"]).to_equal(
        {TEST_AGENT_ID: "Failed to list backups"}
    )


@test
async def agents_list_backups_reauth(
    hass: HomeAssistant = Depends(hass_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test reauthentication is triggered on auth error."""
    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxAuthException("auth failed")
    )

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["backups"]).to_equal([])
    expect(response["result"]["agent_errors"]).to_equal(
        {TEST_AGENT_ID: "Authentication error"}
    )

    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow["step_id"]).to_equal("reauth_confirm")
    expect(flow["handler"]).to_equal(DOMAIN)
    expect(flow["context"]["source"]).to_equal(SOURCE_REAUTH)
    expect(flow["context"]["entry_id"]).to_equal(mock_config_entry.entry_id)


@test.cases(
    test.case("found", backup_id=TEST_AGENT_BACKUP.backup_id),
    test.case("not_found", backup_id="other-backup"),
)
async def agents_get_backup(
    backup_id: str,
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test retrieving a backup's metadata."""
    _setup_list_folder_with_backup(mock_dropbox_client, TEST_AGENT_BACKUP)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    if backup_id == TEST_AGENT_BACKUP.backup_id:
        expect(response["result"]["backup"]).to_equal(TEST_AGENT_BACKUP_RESULT)
    else:
        expect(response["result"]["backup"]).to_be(None)


@test
async def agents_download(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a backup file."""
    tar_name, metadata_name = _suggested_filenames(TEST_AGENT_BACKUP)

    mock_dropbox_client.list_folder = AsyncMock(
        return_value=[
            SimpleNamespace(name=tar_name),
            SimpleNamespace(name=metadata_name),
        ]
    )

    def download_side_effect(path: str) -> AsyncIterator[bytes]:
        if path == f"/{tar_name}":
            return mock_stream(b"backup data")
        return _mock_metadata_stream(TEST_AGENT_BACKUP)

    mock_dropbox_client.download_file = Mock(side_effect=download_side_effect)

    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={TEST_AGENT_ID}"
    )

    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")


@test
async def agents_download_fail(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test handling download failures."""
    # The body-content assertion in the original pytest test relied on the
    # legacy ``enable_event_loop_debug`` autouse fixture which made aiohttp
    # render the traceback into 500 responses. Replicate that here so the
    # assertion remains meaningful under tryke.
    asyncio.get_running_loop().set_debug(True)

    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxUnknownException("boom")
    )

    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={TEST_AGENT_ID}"
    )

    expect(resp.status).to_equal(500)
    body = await resp.content.read()
    expect(b"Failed to get backup" in body).to_be(True)


@test
async def agents_download_not_found(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test download when backup disappears between get and download."""
    tar_name, metadata_name = _suggested_filenames(TEST_AGENT_BACKUP)
    files = [
        SimpleNamespace(name=tar_name),
        SimpleNamespace(name=metadata_name),
    ]

    # First list_folder call (async_get_backup) returns the backup;
    # second call (async_download_backup) returns empty, simulating deletion.
    mock_dropbox_client.list_folder = AsyncMock(side_effect=[files, []])
    mock_dropbox_client.download_file = Mock(
        return_value=_mock_metadata_stream(TEST_AGENT_BACKUP)
    )

    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={TEST_AGENT_ID}"
    )

    expect(resp.status).to_equal(404)
    expect(await resp.content.read()).to_equal(b"")


@test
async def agents_download_file_not_found(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test download when Dropbox file is not found returns 404."""
    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxFileOrFolderNotFoundException("not found")
    )

    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={TEST_AGENT_ID}"
    )

    expect(resp.status).to_equal(404)


@test
async def agents_download_metadata_not_found(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test download when metadata lookup fails."""
    mock_dropbox_client.list_folder = AsyncMock(return_value=[])

    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={TEST_AGENT_ID}"
    )

    expect(resp.status).to_equal(404)
    expect(await resp.content.read()).to_equal(b"")


@test
async def agents_upload(
    hass: HomeAssistant = Depends(hass_fx),
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test uploading a backup to Dropbox."""
    mock_dropbox_client.upload_file = AsyncMock(return_value=None)

    client = await hass_client()

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        resp = await client.post(
            f"/api/backup/upload?agent_id={TEST_AGENT_ID}",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(
        f"Uploading backup {TEST_AGENT_BACKUP.backup_id} to agents" in caplog.text
    ).to_be(True)
    expect(mock_dropbox_client.upload_file.await_count).to_equal(2)


@test
async def agents_upload_fail(
    hass: HomeAssistant = Depends(hass_fx),
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test that backup tar is cleaned up when metadata upload fails."""
    call_count = 0

    async def upload_side_effect(path: str, stream: AsyncIterator[bytes]) -> None:
        nonlocal call_count
        call_count += 1
        async for _ in stream:
            pass
        if call_count == 2:
            raise DropboxUnknownException("metadata upload failed")

    mock_dropbox_client.upload_file = AsyncMock(side_effect=upload_side_effect)
    mock_dropbox_client.delete_file = AsyncMock()

    client = await hass_client()

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        resp = await client.post(
            f"/api/backup/upload?agent_id={TEST_AGENT_ID}",
            data={"file": StringIO("test")},
        )
        await hass.async_block_till_done()

    expect(resp.status).to_equal(201)
    expect("Failed to upload backup" in caplog.text).to_be(True)
    mock_dropbox_client.delete_file.assert_awaited_once()


@test
async def agents_delete(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test deleting a backup."""
    _setup_list_folder_with_backup(mock_dropbox_client, TEST_AGENT_BACKUP)
    mock_dropbox_client.delete_file = AsyncMock(return_value=None)

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": TEST_AGENT_BACKUP.backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"agent_errors": {}})
    expect(mock_dropbox_client.delete_file.await_count).to_equal(2)


@test
async def agents_delete_fail(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test error handling when delete fails."""
    mock_dropbox_client.list_folder = AsyncMock(
        side_effect=DropboxUnknownException("boom")
    )

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": TEST_AGENT_BACKUP.backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {"agent_errors": {TEST_AGENT_ID: "Failed to delete backup"}}
    )


@test
async def agents_delete_not_found(
    mock_dropbox_client: MagicMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test deleting a backup that does not exist."""
    mock_dropbox_client.list_folder = AsyncMock(return_value=[])

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": TEST_AGENT_BACKUP.backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"agent_errors": {}})


@test
async def remove_backup_agents_listener(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test removing a backup agent listener."""
    listener = Mock()
    remove = async_register_backup_agents_listener(hass, listener=listener)

    expect(DATA_BACKUP_AGENT_LISTENERS in hass.data).to_be(True)
    expect(listener in hass.data[DATA_BACKUP_AGENT_LISTENERS]).to_be(True)

    # Remove all other listeners to test the cleanup path.
    hass.data[DATA_BACKUP_AGENT_LISTENERS] = [listener]

    remove()

    expect(DATA_BACKUP_AGENT_LISTENERS not in hass.data).to_be(True)
