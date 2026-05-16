"""Test the backups for WebDAV."""

from collections.abc import AsyncIterator
from copy import deepcopy
from io import StringIO
from unittest.mock import AsyncMock, Mock, patch

from aiowebdav2.exceptions import UnauthorizedError, WebDavError
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import AgentBackup
from homeassistant.components.webdav.backup import async_register_backup_agents_listener
from homeassistant.components.webdav.const import DATA_BACKUP_AGENT_LISTENERS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import json_dumps

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    setup_backup_integration as setup_backup_integration_fx,
    webdav_client as webdav_client_fx,
)
from .const import BACKUP_METADATA

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fx,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    """Module-level anchor fixture."""
    return 0


@test
async def agents_info(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test backup agent info."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "backup.local", "name": "local"},
                {
                    "agent_id": f"{DOMAIN}.{mock_config_entry.entry_id}",
                    "name": mock_config_entry.title,
                },
            ],
        }
    )


@test
async def agents_list_backups(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
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
                    "webdav.01JKXV07ASC62D620DGYNG2R8H": {
                        "protected": False,
                        "size": 34519040,
                    }
                },
                "backup_id": "23e64aec",
                "database_included": True,
                "date": "2025-02-10T17:47:22.727189+01:00",
                "extra_metadata": {},
                "failed_addons": [],
                "failed_agent_ids": [],
                "failed_folders": [],
                "folders": [],
                "homeassistant_included": True,
                "homeassistant_version": "2025.2.1",
                "name": "Automatic backup 2025.2.1",
                "with_automatic_settings": None,
            }
        ]
    )


@test
async def agents_get_backup(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test agent get backup."""
    backup_id = BACKUP_METADATA["backup_id"]
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backup"]).to_equal(
        {
            "addons": [],
            "agents": {
                f"{DOMAIN}.{mock_config_entry.entry_id}": {
                    "protected": False,
                    "size": 34519040,
                }
            },
            "backup_id": "23e64aec",
            "database_included": True,
            "date": "2025-02-10T17:47:22.727189+01:00",
            "extra_metadata": {},
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "folders": [],
            "homeassistant_included": True,
            "homeassistant_version": "2025.2.1",
            "name": "Automatic backup 2025.2.1",
            "with_automatic_settings": None,
        }
    )


@test
async def agents_delete(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
) -> None:
    """Test agent delete backup."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": BACKUP_METADATA["backup_id"],
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})
    expect(webdav_client.clean.call_count).to_equal(2)


@test
async def agents_upload(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test agent upload backup."""
    client = await hass_client()
    test_backup = AgentBackup.from_dict(BACKUP_METADATA)

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
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(webdav_client.upload_iter.call_count).to_equal(2)


@test
async def agents_upload_emits_progress_events(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test upload emits progress events with bytes from upload_iter callbacks."""
    test_backup = AgentBackup.from_dict(BACKUP_METADATA)
    client = await hass_client()
    ws_client = await hass_ws_client(hass)
    observed_progress_bytes: list[int] = []

    await ws_client.send_json_auto_id({"type": "backup/subscribe_events"})
    response = await ws_client.receive_json()
    expect(response["event"]).to_equal({"manager_state": "idle"})
    response = await ws_client.receive_json()
    expect(response["success"]).to_be(True)

    async def _mock_upload_iter(*args: object, **kwargs: object) -> None:
        """Mock upload and trigger progress callback for backup upload."""
        path = args[1]
        if path.endswith(".tar"):
            progress = kwargs.get("progress")
            expect(callable(progress)).to_be_truthy()
            progress(1024, test_backup.size)
            progress(test_backup.size, test_backup.size)

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
        webdav_client.upload_iter.side_effect = _mock_upload_iter
        fetch_backup.return_value = test_backup
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )
        await hass.async_block_till_done()

    expect(resp.status).to_equal(201)

    reached_idle = False
    for _ in range(20):
        response = await ws_client.receive_json()
        event = response.get("event")

        if event is None:
            continue

        if (
            event.get("manager_state") == "receive_backup"
            and event.get("agent_id") == f"{DOMAIN}.{mock_config_entry.entry_id}"
            and "uploaded_bytes" in event
        ):
            observed_progress_bytes.append(event["uploaded_bytes"])

        if event == {"manager_state": "idle"}:
            reached_idle = True
            break

    expect(reached_idle).to_be_truthy()
    expect(1024 in observed_progress_bytes).to_be_truthy()
    expect(test_backup.size in observed_progress_bytes).to_be_truthy()


@test
async def agents_download(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test agent download backup."""
    client = await hass_client()
    backup_id = BACKUP_METADATA["backup_id"]

    resp = await client.get(
        f"/api/backup/download/{backup_id}?agent_id={DOMAIN}.{mock_config_entry.entry_id}"
    )
    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")


@test
async def error_on_agents_download(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we get not found on a not existing backup on download."""
    client = await hass_client()
    backup_id = BACKUP_METADATA["backup_id"]
    webdav_client.list_files.return_value = []

    resp = await client.get(
        f"/api/backup/download/{backup_id}?agent_id={DOMAIN}.{mock_config_entry.entry_id}"
    )
    expect(resp.status).to_equal(404)


@test.cases(
    test.case(
        "webdav_error",
        side_effect=WebDavError("Unknown path"),
        error="Backup operation failed: Unknown path",
    ),
    test.case(
        "timeout",
        side_effect=TimeoutError(),
        error="Backup operation timed out",
    ),
)
async def delete_error(
    side_effect: Exception,
    error: str,
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test error during delete."""
    webdav_client.clean.side_effect = side_effect

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": BACKUP_METADATA["backup_id"],
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {"agent_errors": {f"{DOMAIN}.{mock_config_entry.entry_id}": error}}
    )


@test
async def agents_delete_not_found_does_not_throw(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
) -> None:
    """Test agent delete backup."""
    webdav_client.list_files.return_value = {}
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": BACKUP_METADATA["backup_id"],
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})


@test
async def agents_backup_not_found(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
) -> None:
    """Test backup not found."""
    webdav_client.list_files.return_value = []
    backup_id = BACKUP_METADATA["backup_id"]
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["backup"]).to_be(None)


@test
async def raises_on_403(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we raise on 403."""
    webdav_client.list_files.side_effect = UnauthorizedError(
        "https://webdav.example.com"
    )
    backup_id = BACKUP_METADATA["backup_id"]
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal(
        {f"{DOMAIN}.{mock_config_entry.entry_id}": "Authentication error"}
    )


@test
async def listeners_get_cleaned_up(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test listener gets cleaned up."""
    listener = AsyncMock()
    remove_listener = async_register_backup_agents_listener(hass, listener=listener)

    hass.data[DATA_BACKUP_AGENT_LISTENERS] = [listener]
    remove_listener()

    expect(hass.data.get(DATA_BACKUP_AGENT_LISTENERS)).to_be(None)


@test
async def agents_list_backups_with_multi_chunk_metadata(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test listing backups when metadata is returned in multiple chunks."""
    metadata_json = json_dumps(BACKUP_METADATA).encode()
    mid = len(metadata_json) // 2
    chunk1 = metadata_json[:mid]
    chunk2 = metadata_json[mid:]

    async def _multi_chunk_download(path: str, timeout=None) -> AsyncIterator[bytes]:
        """Mock download returning metadata in multiple chunks."""
        if path.endswith(".json"):
            yield chunk1
            yield chunk2
            return
        yield b"backup data"

    webdav_client.download_iter.side_effect = _multi_chunk_download

    hass.config_entries.async_update_entry(
        mock_config_entry, title=mock_config_entry.title
    )
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    backups = response["result"]["backups"]
    expect(len(backups)).to_equal(1)
    expect(backups[0]["backup_id"]).to_equal(BACKUP_METADATA["backup_id"])
    expect(backups[0]["name"]).to_equal(BACKUP_METADATA["name"])


@test
async def agents_list_backups_skips_invalid_metadata_file(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    webdav_client: AsyncMock = Depends(webdav_client_fx),
) -> None:
    """Test listing backups skips unreadable metadata files."""
    broken_metadata_path = "/broken.metadata.json"
    valid_metadata_path = "/valid.metadata.json"
    valid_backup = deepcopy(BACKUP_METADATA)
    valid_backup["backup_id"] = "valid-backup"
    valid_backup["name"] = "Valid backup"

    webdav_client.list_files.return_value = [broken_metadata_path, valid_metadata_path]

    async def _download_metadata(path: str, timeout=None) -> AsyncIterator[bytes]:
        """Mock metadata downloads with one broken and one valid file."""
        if path == broken_metadata_path:
            yield b""
            return

        if path == valid_metadata_path:
            yield json_dumps(valid_backup).encode()
            return

        yield b"backup data"

    webdav_client.download_iter.side_effect = _download_metadata

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
                    "webdav.01JKXV07ASC62D620DGYNG2R8H": {
                        "protected": False,
                        "size": 34519040,
                    }
                },
                "backup_id": "valid-backup",
                "database_included": True,
                "date": "2025-02-10T17:47:22.727189+01:00",
                "extra_metadata": {},
                "failed_addons": [],
                "failed_agent_ids": [],
                "failed_folders": [],
                "folders": [],
                "homeassistant_included": True,
                "homeassistant_version": "2025.2.1",
                "name": "Valid backup",
                "with_automatic_settings": None,
            }
        ]
    )
