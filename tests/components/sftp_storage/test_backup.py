"""Test the Backup SFTP Location platform."""

from io import StringIO
import json
from typing import Any
from unittest.mock import MagicMock, patch

from asyncssh.sftp import SFTPError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sftp_storage.backup import (
    async_register_backup_agents_listener,
)
from homeassistant.components.sftp_storage.const import (
    DATA_BACKUP_AGENT_LISTENERS,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    BACKUP_METADATA,
    CONFIG_ENTRY_TITLE,
    TEST_AGENT_BACKUP,
    TEST_AGENT_ID,
    hass as hass_fx,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
    setup_integration as setup_integration_fx,
)
from .asyncssh_mock import SSHClientConnectionMock

from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
)


# Required for async tests with Depends.
@fixture
def _trigger_executor() -> int:
    return 0


def generate_result(metadata: dict) -> dict:
    """Generate an expected result from metadata."""
    expected_result: dict = metadata["metadata"].copy()
    expected_result["agents"] = {
        f"{DOMAIN}.{TEST_AGENT_ID}": {
            "protected": expected_result.pop("protected"),
            "size": expected_result.pop("size"),
        }
    }
    expected_result.update(
        {
            "failed_addons": [],
            "failed_agent_ids": [],
            "failed_folders": [],
            "with_automatic_settings": None,
        }
    )
    return expected_result


@test
async def agents_info(
    hass: HomeAssistant = Depends(hass_fx),
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test backup agent info."""
    client = await hass_ws_client()

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        {
            "agents": [
                {"agent_id": "backup.local", "name": "local"},
                {"agent_id": f"{DOMAIN}.{TEST_AGENT_ID}", "name": CONFIG_ENTRY_TITLE},
            ],
        }
    )

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_unload(config_entry.entry_id)

    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(
        response["result"]
        == {"agents": [{"agent_id": "backup.local", "name": "local"}]}
        or config_entry.state == ConfigEntryState.NOT_LOADED
    ).to_be(True)


@test
async def agents_list_backups(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent list backups."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)
    expected_result = generate_result(BACKUP_METADATA)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal([expected_result])


@test
async def agents_list_backups_fail(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent list backups fails."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)
    mock_ssh_connection._sftp._mock_open._mock_read.side_effect = SFTPError(
        2, "Error message"
    )

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["backups"]).to_equal([])
    expect(response["result"]["agent_errors"]).to_equal(
        {
            f"{DOMAIN}.{TEST_AGENT_ID}": "Remote server error while attempting to list backups: Error message"
        }
    )


@test
async def agents_list_backups_include_bad_metadata(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test agent list backups."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA, with_bad=True)
    expected_result = generate_result(BACKUP_METADATA)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/info"})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["agent_errors"]).to_equal({})
    expect(response["result"]["backups"]).to_equal([expected_result])
    # Called two times, one for bad backup metadata and once for good
    expect(mock_ssh_connection._sftp._mock_open._mock_read.call_count).to_equal(2)
    expect(
        "Failed to load backup metadata from file: /backup_location/invalid.metadata.json. Expecting value: line 1 column 1 (char 0)"
        in caplog.messages
    ).to_be(True)


@test.cases(
    test.case(
        "found",
        backup_id=TEST_AGENT_BACKUP.backup_id,
        expected_result=generate_result(BACKUP_METADATA),
    ),
    test.case("not_found", backup_id="12345", expected_result=None),
)
async def agents_get_backup(
    backup_id: str,
    expected_result: dict[str, Any] | None,
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent get backup."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

    client = await hass_ws_client()
    await client.send_json_auto_id({"type": "backup/details", "backup_id": backup_id})
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]["backup"]).to_equal(expected_result)


@test
async def agents_download(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test agent download backup."""
    client = await hass_client()
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={DOMAIN}.{TEST_AGENT_ID}"
    )
    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")
    mock_ssh_connection._sftp._mock_open.close.assert_awaited()


@test
async def agents_download_fail(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test agent download backup fails."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

    # This will cause `FileNotFoundError` exception in `BackupAgentClient.iter_file() method.`
    mock_ssh_connection._sftp._mock_exists.side_effect = [True, False]
    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={DOMAIN}.{TEST_AGENT_ID}"
    )
    expect(resp.status).to_equal(404)

    # This will raise `RuntimeError` causing Internal Server Error, mimicking that the SFTP setup failed.
    mock_ssh_connection._sftp = None
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={DOMAIN}.{TEST_AGENT_ID}"
    )
    expect(resp.status).to_equal(500)
    content = await resp.content.read()
    expect(b"Internal Server Error" in content).to_be(True)


@test
async def agents_download_metadata_not_found(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test agent download backup raises error if not found."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

    mock_ssh_connection._sftp._mock_exists.return_value = False
    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{TEST_AGENT_BACKUP.backup_id}?agent_id={DOMAIN}.{TEST_AGENT_ID}"
    )
    expect(resp.status).to_equal(404)
    content = await resp.content.read()
    expect(content.decode()).to_equal("")


@test
async def agents_upload(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test agent upload backup."""
    client = await hass_client()

    with (
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
    ):
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{TEST_AGENT_ID}",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(
        f"Uploading backup: {TEST_AGENT_BACKUP.backup_id}" in caplog.text
    ).to_be(True)
    expect(
        f"Successfully uploaded backup id: {TEST_AGENT_BACKUP.backup_id}"
        in caplog.text
    ).to_be(True)
    # Called write 2 times
    # 1. When writing backup file
    # 2. When writing metadata file
    expect(mock_ssh_connection._sftp._mock_open._mock_write.call_count).to_equal(2)

    # This is 'backup file'
    expect(
        b"test"
        in mock_ssh_connection._sftp._mock_open._mock_write.call_args_list[0].args
    ).to_be(True)

    # This is backup metadata
    uploaded_metadata = json.loads(
        mock_ssh_connection._sftp._mock_open._mock_write.call_args_list[1].args[0]
    )["metadata"]
    expect(uploaded_metadata).to_equal(BACKUP_METADATA["metadata"])


@test
async def agents_upload_fail(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test agent upload backup fails."""
    client = await hass_client()
    mock_ssh_connection._sftp._mock_open._mock_write.side_effect = SFTPError(
        2, "Error message"
    )

    with (
        patch(
            "homeassistant.components.backup.manager.read_backup",
            return_value=TEST_AGENT_BACKUP,
        ),
    ):
        resp = await client.post(
            f"/api/backup/upload?agent_id={DOMAIN}.{TEST_AGENT_ID}",
            data={"file": StringIO("test")},
        )

    expect(resp.status).to_equal(201)
    expect(
        f"Unexpected error for {DOMAIN}.{TEST_AGENT_ID}: Error message"
        in caplog.messages
    ).to_be(True)


@test
async def agents_delete(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent delete backup."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

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

    # Called 2 times, to remove metadata and backup file.
    expect(mock_ssh_connection._sftp._mock_unlink.call_count).to_equal(2)


@test.cases(
    test.case(
        "file_not_found_exc",
        exists_side_effect=[True, False],
        expected_result={"agent_errors": {}},
    ),
    test.case(
        "sftp_error_exc",
        exists_side_effect=SFTPError(0, "manual"),
        expected_result={
            "agent_errors": {
                f"{DOMAIN}.{TEST_AGENT_ID}": f"Failed to delete backup id: {TEST_AGENT_BACKUP.backup_id}: manual"
            }
        },
    ),
)
async def agents_delete_fail(
    exists_side_effect: list[bool] | Exception,
    expected_result: dict[str, dict[str, str]],
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent delete backup fails."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)
    mock_ssh_connection._sftp._mock_exists.side_effect = exists_side_effect

    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": TEST_AGENT_BACKUP.backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(expected_result)


@test
async def agents_delete_not_found(
    mock_ssh_connection: SSHClientConnectionMock = Depends(setup_integration_fx),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test agent delete backup not found."""
    mock_ssh_connection.mock_setup_backup(BACKUP_METADATA)

    client = await hass_ws_client()
    backup_id = "1234"

    await client.send_json_auto_id(
        {
            "type": "backup/delete",
            "backup_id": backup_id,
        }
    )
    response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"agent_errors": {}})


@test
async def listeners_get_cleaned_up(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test listener gets cleaned up."""
    listener = MagicMock()
    remove_listener = async_register_backup_agents_listener(hass, listener=listener)

    hass.data[DATA_BACKUP_AGENT_LISTENERS] = [
        listener
    ]  # make sure it's the last listener
    remove_listener()

    expect(DATA_BACKUP_AGENT_LISTENERS not in hass.data).to_be(True)
