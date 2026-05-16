"""Test the Cloudflare R2 backup platform."""

from collections.abc import AsyncIterator
from io import StringIO
import json
from time import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from botocore.exceptions import BotoCoreError, ConnectTimeoutError
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import (
    AgentBackup,
    DATA_MANAGER,
    UploadBackupEvent,
)
from homeassistant.components.cloudflare_r2.backup import (
    MULTIPART_MIN_PART_SIZE_BYTES,
    R2BackupAgent,
    async_register_backup_agents_listener,
    suggested_filenames,
)
from homeassistant.components.cloudflare_r2.const import (
    CONF_ENDPOINT_URL,
    DATA_BACKUP_AGENT_LISTENERS,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_client as mock_client_fx,
    mock_client_large as mock_client_large_fx,
    mock_client_xlarge as mock_client_xlarge_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_config_entry_with_prefix as mock_config_entry_with_prefix_fx,
    setup_backup_integration as setup_backup_integration_fx,
    setup_backup_integration_large as setup_backup_integration_large_fx,
    setup_backup_integration_xlarge as setup_backup_integration_xlarge_fx,
    test_backup as test_backup_fx,
    test_backup_large as test_backup_large_fx,
    test_backup_xlarge as test_backup_xlarge_fx,
)
from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
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
async def suggested_filenames_test(
    _trigger: int = Depends(_trigger_executor),
) -> None:
    """Test the suggested_filenames function."""
    backup = AgentBackup(
        backup_id="a1b2c3",
        date="2021-01-01T01:02:03+00:00",
        addons=[],
        database_included=False,
        extra_metadata={},
        folders=[],
        homeassistant_included=False,
        homeassistant_version=None,
        name="my_pretty_backup",
        protected=False,
        size=0,
    )
    tar_filename, metadata_filename = suggested_filenames(backup)

    expect(tar_filename).to_equal("my_pretty_backup_2021-01-01_01.02_03000000.tar")
    expect(metadata_filename).to_equal(
        "my_pretty_backup_2021-01-01_01.02_03000000.metadata.json"
    )


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
    test_backup: AgentBackup = Depends(test_backup_fx),
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
                "addons": test_backup.addons,
                "agents": {
                    f"{DOMAIN}.{mock_config_entry.entry_id}": {
                        "protected": test_backup.protected,
                        "size": test_backup.size,
                    }
                },
                "backup_id": test_backup.backup_id,
                "database_included": test_backup.database_included,
                "date": test_backup.date,
                "extra_metadata": test_backup.extra_metadata,
                "failed_addons": [],
                "failed_agent_ids": [],
                "failed_folders": [],
                "folders": test_backup.folders,
                "homeassistant_included": test_backup.homeassistant_included,
                "homeassistant_version": test_backup.homeassistant_version,
                "name": test_backup.name,
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
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test agent get backup."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "backup/details", "backup_id": test_backup.backup_id}
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backup"]).to_equal(
        {
            "addons": test_backup.addons,
            "agents": {
                f"{DOMAIN}.{mock_config_entry.entry_id}": {
                    "protected": test_backup.protected,
                    "size": test_backup.size,
                }
            },
            "backup_id": test_backup.backup_id,
            "database_included": test_backup.database_included,
            "date": test_backup.date,
            "extra_metadata": test_backup.extra_metadata,
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "folders": test_backup.folders,
            "homeassistant_included": test_backup.homeassistant_included,
            "homeassistant_version": test_backup.homeassistant_version,
            "name": test_backup.name,
            "with_automatic_settings": None,
        }
    )


@test
async def agents_get_backup_does_not_throw_on_not_found(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
) -> None:
    """Test agent get backup does not throw on a backup not found."""
    mock_client.list_objects_v2.return_value = {"Contents": []}

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "backup/details", "backup_id": "random"})
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backup"]).to_be(None)


@test
async def agents_list_backups_with_corrupted_metadata(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    caplog: LogCapture = Depends(caplog_fx),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test listing backups when one metadata file is corrupted."""
    agent = R2BackupAgent(hass, mock_config_entry)

    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {
                "Key": "valid_backup.metadata.json",
                "LastModified": "2023-01-01T00:00:00+00:00",
            },
            {
                "Key": "corrupted_backup.metadata.json",
                "LastModified": "2023-01-01T00:00:00+00:00",
            },
        ]
    }

    valid_metadata = json.dumps(test_backup.as_dict())
    corrupted_metadata = "{invalid json content"

    async def mock_get_object(**kwargs):
        """Mock get_object with different responses based on the key."""
        key = kwargs.get("Key", "")
        if "valid_backup" in key:
            mock_body = AsyncMock()
            mock_body.read.return_value = valid_metadata.encode()
            return {"Body": mock_body}
        mock_body = AsyncMock()
        mock_body.read.return_value = corrupted_metadata.encode()
        return {"Body": mock_body}

    mock_client.get_object.side_effect = mock_get_object

    backups = await agent.async_list_backups()
    expect(len(backups)).to_equal(1)
    expect(backups[0].backup_id).to_equal(test_backup.backup_id)
    expect("Failed to process metadata file" in caplog.text).to_be_truthy()


@test
async def agents_delete(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
) -> None:
    """Test agent delete backup."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": "23e64aec",
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})
    expect(mock_client.delete_object.call_count).to_equal(2)


@test
async def agents_delete_not_throwing_on_not_found(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
) -> None:
    """Test agent delete backup does not throw on a backup not found."""
    mock_client.list_objects_v2.return_value = {"Contents": []}

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": "random",
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal({"agent_errors": {}})
    expect(mock_client.delete_object.call_count).to_equal(0)


@test
async def agents_upload(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test agent upload backup (small/single-part)."""
    client = await hass_client()
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=test_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(
            side_effect=[
                b"a" * test_backup.size,
                b"appendix",
                b"",
            ]
        )
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

        expect(resp.status).to_equal(201)
        expect(f"Uploading backup {test_backup.backup_id}" in caplog.text).to_be_truthy()
        # single part + metadata both as regular upload (no multiparts)
        expect(mock_client.create_multipart_upload.await_count).to_equal(0)
        expect(mock_client.put_object.await_count).to_equal(2)


@test
async def agents_upload_large(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_large_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    mock_client: AsyncMock = Depends(mock_client_large_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    test_backup: AgentBackup = Depends(test_backup_large_fx),
) -> None:
    """Test agent upload backup (large/multipart)."""
    client = await hass_client()
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=test_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(
            side_effect=[
                b"a" * test_backup.size,
                b"appendix",
                b"",
            ]
        )
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

        expect(resp.status).to_equal(201)
        expect(f"Uploading backup {test_backup.backup_id}" in caplog.text).to_be_truthy()
        expect("Uploading final part" in caplog.text).to_be_truthy()
        # 2 parts as multipart + metadata as regular upload
        expect(mock_client.create_multipart_upload.await_count).to_equal(1)
        expect(mock_client.upload_part.await_count).to_equal(2)
        expect(mock_client.complete_multipart_upload.await_count).to_equal(1)
        expect(mock_client.put_object.await_count).to_equal(1)


@test
async def agents_upload_network_failure(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test agent upload backup with network failure."""
    client = await hass_client()
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=test_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(side_effect=[b"test", b""])
        mock_client.put_object.side_effect = mock_client.upload_part.side_effect = (
            mock_client.abort_multipart_upload.side_effect
        ) = ConnectTimeoutError(endpoint_url=USER_INPUT[CONF_ENDPOINT_URL])
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect("Upload failed for cloudflare_r2" in caplog.text).to_be_truthy()


@test
async def multipart_upload_consistent_part_sizes(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test that multipart upload uses consistent part sizes."""
    agent = R2BackupAgent(hass, mock_config_entry)

    # simulate varying chunk data sizes
    # total data: 12 + 12 + 10 + 12 + 5 = 51 MiB
    chunk_sizes = [12, 12, 10, 12, 5]  # in units of 1 MiB
    mib = 2**20

    async def mock_stream():
        for size in chunk_sizes:
            yield b"x" * (size * mib)

    async def open_stream():
        return mock_stream()

    uploaded_part_sizes: list[int] = []

    async def record_upload_part(**kwargs):
        body = kwargs.get("Body", b"")
        uploaded_part_sizes.append(len(body))
        return {"ETag": f"etag-{len(uploaded_part_sizes)}"}

    mock_client.upload_part.side_effect = record_upload_part

    await agent._upload_multipart("test.tar", open_stream, Mock())

    expect(len(uploaded_part_sizes) >= 2).to_be_truthy()
    non_trailing_parts = uploaded_part_sizes[:-1]
    expect(
        all(size == MULTIPART_MIN_PART_SIZE_BYTES for size in non_trailing_parts)
    ).to_be_truthy()

    total_data = sum(chunk_sizes) * mib
    expected_trailing = total_data % MULTIPART_MIN_PART_SIZE_BYTES
    if expected_trailing == 0:
        expected_trailing = MULTIPART_MIN_PART_SIZE_BYTES
    expect(uploaded_part_sizes[-1]).to_equal(expected_trailing)


@test
async def agents_upload_on_progress(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_xlarge_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    mock_client: AsyncMock = Depends(mock_client_xlarge_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    test_backup: AgentBackup = Depends(test_backup_xlarge_fx),
) -> None:
    """Test agent upload backup emits UploadBackupEvent via on_progress."""
    client = await hass_client()

    manager = hass.data[DATA_MANAGER]
    events: list[UploadBackupEvent] = []

    def _collect(event: UploadBackupEvent) -> None:
        if isinstance(event, UploadBackupEvent):
            events.append(event)

    unsub = manager.async_subscribe_events(_collect)

    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backup",
            return_value=test_backup,
        ),
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=test_backup,
        ),
        patch("pathlib.Path.open") as mocked_open,
    ):
        mocked_open.return_value.read = Mock(
            side_effect=[
                b"a" * test_backup.size,
                b"",
            ]
        )
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{mock_config_entry.entry_id}",
            data={"file": StringIO("test")},
        )

    unsub()

    expect(resp.status).to_equal(201)
    agent_id = f"{DOMAIN}.{mock_config_entry.entry_id}"
    agent_events = [e for e in events if e.agent_id == agent_id]
    expect(len(agent_events) >= 2).to_be_truthy()
    expect(all(e.total_bytes == test_backup.size for e in agent_events)).to_be_truthy()
    uploaded_bytes = [e.uploaded_bytes for e in agent_events]
    expect(uploaded_bytes).to_equal(sorted(uploaded_bytes))
    expect(len(set(uploaded_bytes))).to_equal(len(uploaded_bytes))
    expect(agent_events[0].uploaded_bytes < agent_events[0].total_bytes).to_be_truthy()


@test
async def agents_download(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test agent download backup."""
    client = await hass_client()
    backup_id = "23e64aec"

    resp = await client.get(
        f"/api/backup/download/{backup_id}?agent_id={DOMAIN}.{mock_config_entry.entry_id}"
    )
    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")
    # One for metadata, one for tar file
    expect(mock_client.get_object.call_count).to_equal(2)


@test
async def error_during_delete(
    _trigger: int = Depends(_trigger_executor),
    _setup: None = Depends(setup_backup_integration_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test the error wrapper."""
    mock_client.delete_object.side_effect = BotoCoreError

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": test_backup.backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be_truthy()
    expect(response["result"]).to_equal(
        {
            "agent_errors": {
                f"{DOMAIN}.{mock_config_entry.entry_id}": "Failed during async_delete_backup"
            }
        }
    )


@test
async def cache_expiration(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test that the cache expires correctly."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"bucket": "test-bucket"},
        unique_id="test-unique-id",
        title="Test R2",
    )
    mock_entry.runtime_data = mock_client

    agent = R2BackupAgent(hass, mock_entry)

    metadata_content = json.dumps(test_backup.as_dict())
    mock_body = AsyncMock()
    mock_body.read.return_value = metadata_content.encode()
    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "test.metadata.json", "LastModified": "2023-01-01T00:00:00+00:00"}
        ]
    }

    await agent.async_list_backups()
    expect(mock_client.list_objects_v2.call_count).to_equal(1)
    expect(mock_client.get_object.call_count).to_equal(1)

    await agent.async_list_backups()
    expect(mock_client.list_objects_v2.call_count).to_equal(1)
    expect(mock_client.get_object.call_count).to_equal(1)

    agent._cache_expiration = time() - 1

    await agent.async_list_backups()
    expect(mock_client.list_objects_v2.call_count).to_equal(2)
    expect(mock_client.get_object.call_count).to_equal(2)


@test
async def listeners_get_cleaned_up(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test listener gets cleaned up."""
    listener = MagicMock()
    remove_listener = async_register_backup_agents_listener(hass, listener=listener)

    hass.data[DATA_BACKUP_AGENT_LISTENERS] = [listener]
    remove_listener()

    expect(DATA_BACKUP_AGENT_LISTENERS not in hass.data).to_be_truthy()


@test
async def multipart_upload_uses_prefix_for_all_calls(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry_with_prefix: MockConfigEntry = Depends(
        mock_config_entry_with_prefix_fx
    ),
) -> None:
    """Test multipart upload uses the configured prefix for all S3 calls."""
    mock_config_entry_with_prefix.runtime_data = mock_client
    agent = R2BackupAgent(hass, mock_config_entry_with_prefix)

    async def stream() -> AsyncIterator[bytes]:
        # Force multipart: > MIN_PART_SIZE
        yield b"x" * (MULTIPART_MIN_PART_SIZE_BYTES + 1)

    async def open_stream():
        return stream()

    await agent._upload_multipart("test.tar", open_stream, Mock())

    prefixed_key = "ha/backups/test.tar"

    expect(mock_client.create_multipart_upload.await_args.kwargs["Key"]).to_equal(
        prefixed_key
    )

    for call in mock_client.upload_part.await_args_list:
        expect(call.kwargs["Key"]).to_equal(prefixed_key)

    expect(mock_client.complete_multipart_upload.await_args.kwargs["Key"]).to_equal(
        prefixed_key
    )


@test
async def list_backups_passes_prefix_to_list_objects(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    mock_client: AsyncMock = Depends(mock_client_fx),
    mock_config_entry_with_prefix: MockConfigEntry = Depends(
        mock_config_entry_with_prefix_fx
    ),
    test_backup: AgentBackup = Depends(test_backup_fx),
) -> None:
    """Test list_objects_v2 is called with Prefix when configured."""
    mock_config_entry_with_prefix.runtime_data = mock_client
    agent = R2BackupAgent(hass, mock_config_entry_with_prefix)

    tar_filename, metadata_filename = suggested_filenames(test_backup)
    mock_client.list_objects_v2.return_value = {
        "Contents": [
            {"Key": f"ha/backups/{metadata_filename}"},
            {"Key": f"ha/backups/{tar_filename}"},
        ]
    }

    await agent.async_list_backups()

    expect(mock_client.list_objects_v2.call_args.kwargs["Prefix"]).to_equal(
        "ha/backups/"
    )
