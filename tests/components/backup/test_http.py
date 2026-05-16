"""Tests for the Backup integration."""

import asyncio
from collections.abc import AsyncIterator
from io import BytesIO, StringIO
import json
from pathlib import Path
import re
import tarfile
from typing import Any
from unittest.mock import patch

from aiohttp import web
from aiohttp.hdrs import CONTENT_DISPOSITION, CONTENT_TYPE
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import (
    AddonInfo,
    AgentBackup,
    BackupAgentError,
    BackupNotFound,
    Folder,
)
from homeassistant.components.backup.const import DOMAIN
from homeassistant.core import HomeAssistant

from ._fixtures import (
    hass as hass_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_client as hass_client_fx,
    mock_backups as mock_backups_fx,
)
from .common import (
    TEST_BACKUP_ABC123,
    TEST_BACKUP_PATH_ABC123,
    aiter_from_iter,
    setup_backup_integration,
)

from tests.common import MockUser, get_fixture_path
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


PROTECTED_BACKUP = AgentBackup(
    addons=[AddonInfo(name="Test", slug="test", version="1.0.0")],
    backup_id="c0cb53bd",
    database_included=True,
    date="1970-01-01T00:00:00Z",
    extra_metadata={},
    folders=[Folder.MEDIA, Folder.SHARE],
    homeassistant_included=True,
    homeassistant_version="2024.12.0",
    name="Test",
    protected=True,
    size=13,
)


def _install_backup_abc123(hass: HomeAssistant) -> None:
    """Copy the abc123 backup fixture into the hass backup dir."""
    (get_fixture_path("test_backups", DOMAIN) / TEST_BACKUP_PATH_ABC123).copy_into(
        Path(hass.config.path("backups"))
    )


@test
async def downloading_local_backup(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a local backup file."""
    _install_backup_abc123(hass)
    await setup_backup_integration(hass)

    client = await hass_client()

    resp = await client.get("/api/backup/download/abc123?agent_id=backup.local")
    expect(resp.status).to_equal(200)


@test
async def downloading_remote_backup(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a remote backup."""
    await setup_backup_integration(
        hass, backups={"test.test": [TEST_BACKUP_ABC123]}, remote_agents=["test.test"]
    )

    client = await hass_client()

    resp = await client.get("/api/backup/download/abc123?agent_id=test.test")
    expect(resp.status).to_equal(200)
    expect(await resp.content.read()).to_equal(b"backup data")


@test
async def downloading_local_encrypted_backup_file_not_found(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a missing local backup file."""
    _install_backup_abc123(hass)
    await setup_backup_integration(hass)
    client = await hass_client()

    Path(hass.config.path("backups/abc123.tar")).unlink()

    resp = await client.get(
        "/api/backup/download/abc123?agent_id=backup.local&password=blah"
    )
    expect(resp.status).to_equal(404)


@test
async def downloading_local_encrypted_backup(
    _mock_backups: None = Depends(mock_backups_fx),
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a local backup file."""
    await setup_backup_integration(hass)
    await _test_downloading_encrypted_backup(hass_client, "backup.local")


@test
async def downloading_remote_encrypted_backup(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a local backup file."""
    backup_path = get_fixture_path("test_backups/c0cb53bd.tar", DOMAIN)
    mock_agents = await setup_backup_integration(
        hass, remote_agents=["test.test"], backups={"test.test": [PROTECTED_BACKUP]}
    )

    async def download_backup(backup_id: str, **kwargs: Any) -> AsyncIterator[bytes]:
        return aiter_from_iter((backup_path.read_bytes(),))

    mock_agents["test.test"].async_download_backup.side_effect = download_backup
    await _test_downloading_encrypted_backup(hass_client, "test.test")


@test.cases(
    test.case("agent_error", error=BackupAgentError, status=500),
    test.case("not_found", error=BackupNotFound, status=404),
)
async def downloading_remote_encrypted_backup_with_error(
    error: type[Exception],
    status: int,
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a local backup file."""
    mock_agents = await setup_backup_integration(
        hass, remote_agents=["test.test"], backups={"test.test": [PROTECTED_BACKUP]}
    )

    mock_agents["test.test"].async_download_backup.side_effect = error
    client = await hass_client()
    resp = await client.get(
        f"/api/backup/download/{PROTECTED_BACKUP.backup_id}?agent_id=test.test&password=blah"
    )
    expect(resp.status).to_equal(status)


async def _test_downloading_encrypted_backup(
    hass_client: ClientSessionGenerator,
    agent_id: str,
) -> None:
    """Test downloading an encrypted backup file."""

    def assert_tar_download_response(resp: web.Response) -> None:
        expect(resp.status).to_equal(200)
        expect(resp.headers.get(CONTENT_TYPE, "")).to_equal("application/x-tar")
        expect(
            bool(
                re.match(
                    r"attachment; filename=.*\.tar",
                    resp.headers.get(CONTENT_DISPOSITION, ""),
                )
            )
        ).to_be(True)

    # Try downloading without supplying a password
    client = await hass_client()
    resp = await client.get(f"/api/backup/download/c0cb53bd?agent_id={agent_id}")
    assert_tar_download_response(resp)

    backup = await resp.read()
    # We expect a valid outer tar file, but the inner tar file is encrypted and
    # can't be read
    with tarfile.open(fileobj=BytesIO(backup), mode="r") as outer_tar:
        enc_metadata = json.loads(outer_tar.extractfile("./backup.json").read())
        expect(enc_metadata["protected"]).to_be(True)
        with outer_tar.extractfile("homeassistant.tar.gz") as inner_tar_file:
            expect(
                lambda: tarfile.open(fileobj=inner_tar_file, mode="r")
            ).to_raise(tarfile.ReadError, match="file could not be opened")

    # Download with the wrong password
    resp = await client.get(
        f"/api/backup/download/c0cb53bd?agent_id={agent_id}&password=wrong"
    )
    assert_tar_download_response(resp)
    backup = await resp.read()
    # We expect a truncated outer tar file
    with tarfile.open(fileobj=BytesIO(backup), mode="r") as outer_tar:
        expect(lambda: outer_tar.getnames()).to_raise(
            tarfile.ReadError, match="unexpected end of data"
        )

    # Finally download with the correct password
    resp = await client.get(
        f"/api/backup/download/c0cb53bd?agent_id={agent_id}&password=hunter2"
    )
    assert_tar_download_response(resp)
    backup = await resp.read()
    # We expect a valid outer tar file, the inner tar file is decrypted and can be read
    with tarfile.open(fileobj=BytesIO(backup), mode="r") as outer_tar:
        dec_metadata = json.loads(outer_tar.extractfile("./backup.json").read())
        expect(dec_metadata).to_equal(enc_metadata | {"protected": False})
        with (
            outer_tar.extractfile("homeassistant.tar.gz") as inner_tar_file,
            tarfile.open(fileobj=inner_tar_file, mode="r") as inner_tar,
        ):
            expect(inner_tar.getnames()).to_equal(
                [
                    ".",
                    "README.md",
                    "test_symlink",
                    "test1",
                    "test1/script.sh",
                ]
            )


@test
async def downloading_backup_not_found(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test downloading a backup file that does not exist."""
    await setup_backup_integration(hass)

    client = await hass_client()

    resp = await client.get("/api/backup/download/abc1234?agent_id=backup.local")
    expect(resp.status).to_equal(404)


@test
async def downloading_backup_not_found_get_backup_returns_none(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test downloading a backup file that does not exist."""
    mock_agents = await setup_backup_integration(hass, remote_agents=["test.test"])
    mock_agents["test.test"].async_get_backup.return_value = None
    mock_agents["test.test"].async_get_backup.side_effect = None

    client = await hass_client()

    resp = await client.get("/api/backup/download/abc123?agent_id=test.test")
    expect(resp.status).to_equal(404)
    expect(
        "Detected that integration 'test' returns None from BackupAgent.async_get_backup."
        in caplog.text
    ).to_be(True)


@test
async def downloading_as_non_admin(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test downloading a backup file when you are not an admin."""
    hass_admin_user.groups = []
    await setup_backup_integration(hass)

    client = await hass_client()

    resp = await client.get("/api/backup/download/abc123?agent_id=backup.local")
    expect(resp.status).to_equal(401)


@test
async def uploading_a_backup_file(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test uploading a backup file."""
    await setup_backup_integration(hass)

    client = await hass_client()

    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_receive_backup",
        return_value=TEST_BACKUP_ABC123.backup_id,
    ) as async_receive_backup_mock:
        resp = await client.post(
            "/api/backup/upload?agent_id=backup.local",
            data={"file": StringIO("test")},
        )
        expect(resp.status).to_equal(201)
        expect(await resp.json()).to_equal({"backup_id": TEST_BACKUP_ABC123.backup_id})
        expect(async_receive_backup_mock.called).to_be(True)


@test.cases(
    test.case(
        "os_error",
        error=OSError("Boom!"),
        message="Can't write backup file: Boom!",
    ),
    test.case(
        "cancelled",
        error=asyncio.CancelledError("Boom!"),
        message="",
    ),
)
async def error_handling_uploading_a_backup_file(
    error: Exception,
    message: str,
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test error handling when uploading a backup file."""
    await setup_backup_integration(hass)

    client = await hass_client()

    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_receive_backup",
        side_effect=error,
    ):
        resp = await client.post(
            "/api/backup/upload?agent_id=backup.local",
            data={"file": StringIO("test")},
        )
        expect(resp.status).to_equal(500)
        expect(await resp.text()).to_equal(message)
