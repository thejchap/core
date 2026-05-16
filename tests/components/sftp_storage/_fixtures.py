"""Tryke fixtures for the SFTP Storage integration."""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

from asyncssh import generate_private_key
from tryke import Depends, fixture

import homeassistant.core as ha
from homeassistant.components.backup import DOMAIN as BACKUP_DOMAIN, AgentBackup
from homeassistant.components.sftp_storage import SFTPConfigEntryData
from homeassistant.components.sftp_storage.const import (
    CONF_BACKUP_LOCATION,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PRIVATE_KEY_FILE,
    CONF_USERNAME,
    DEFAULT_PKEY_NAME,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame, translation as translation_helper
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.setup import async_setup_component
from homeassistant.util.async_ import create_eager_task
from homeassistant.util.ulid import ulid

from .asyncssh_mock import SSHClientConnectionMock, async_context_manager

from tests.common import MockConfigEntry, MockUser, async_test_home_assistant
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aiohttp_client as aiohttp_client_fx,
    hass_storage as hass_storage_fx,
    load_registries as load_registries_fx,
    tmp_path as tmp_path_fx,
)

type ComponentSetup = Callable[[], Awaitable[None]]

BACKUP_METADATA = {
    "file_path": "/backup_location/backup.tar",
    "metadata": {
        "addons": [{"name": "Test", "slug": "test", "version": "1.0.0"}],
        "backup_id": "test-backup",
        "date": "2025-01-01T01:23:45.687000+01:00",
        "database_included": True,
        "extra_metadata": {
            "instance_id": 1,
            "with_automatic_settings": False,
            "supervisor.backup_request_date": "2025-01-01T01:23:45.687000+01:00",
        },
        "folders": [],
        "homeassistant_included": True,
        "homeassistant_version": "2024.12.0",
        "name": "Test",
        "protected": True,
        "size": 1234,
    },
}
TEST_AGENT_BACKUP = AgentBackup.from_dict(BACKUP_METADATA["metadata"])

CONFIG_ENTRY_TITLE = "testsshuser@127.0.0.1"
PRIVATE_KEY_FILE_UUID = "0123456789abcdef0123456789abcdef"
TEST_AGENT_ID = ulid()


# Per-test tmp config dir isolates state across tests (matches the pytest
# ``hass_tmp_config_dir`` pattern; without it, parallel tests share
# ``testing_config/tmp_backups`` which races backup-upload state).


@fixture
def hass_config_dir(tmp_path: Path = Depends(tmp_path_fx)) -> str:
    """Override the default hass config dir with a per-test tmp dir."""
    return str(tmp_path)


@fixture
async def hass(
    load_registries: bool = Depends(load_registries_fx),
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> AsyncGenerator[HomeAssistant]:
    """Provide a hass instance backed by a per-test tmp config dir."""
    del hass_storage  # side-effect fixture; storage patch already active
    loop = asyncio.get_running_loop()
    exceptions: list[BaseException] = []

    def exc_handle(
        loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ) -> None:
        if "exception" in context:
            exceptions.append(context["exception"])
        else:
            exceptions.append(
                Exception(
                    "Received exception handler without exception, "
                    f"but with message: {context['message']}"
                )
            )
        if orig_exception_handler is not None:
            orig_exception_handler(loop, context)
        else:
            loop.default_exception_handler(context)

    async with async_test_home_assistant(
        loop, load_registries, config_dir=hass_config_dir
    ) as hass_inst:
        orig_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(exc_handle)
        frame.async_setup(hass_inst)
        hass_inst._captured_loop_exceptions = exceptions  # type: ignore[attr-defined]
        await translation_helper.async_load_integrations(hass_inst, {ha.DOMAIN})

        yield hass_inst

        loaded_entries = [
            entry
            for entry in hass_inst.config_entries.async_entries()
            if entry.state is ConfigEntryState.LOADED
        ]
        if loaded_entries:
            await asyncio.gather(
                *(
                    create_eager_task(
                        hass_inst.config_entries.async_unload(entry.entry_id),
                        loop=hass_inst.loop,
                    )
                    for entry in loaded_entries
                )
            )
        await hass_inst.async_stop(force=True)

    for ex in exceptions:
        msg = str(ex)
        if isinstance(ex, RuntimeError) and (
            "Event loop is closed" in msg or "Loop is closed" in msg
        ):
            continue
        raise ex


def _create_private_key_file(hass: HomeAssistant) -> str:
    """Create a private key file in the integration storage directory."""
    key_dest_path = Path(hass.config.path(STORAGE_DIR, DOMAIN))
    dest_file = key_dest_path / f".{ulid()}_{DEFAULT_PKEY_NAME}"
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    dest_file.write_bytes(
        generate_private_key("ssh-rsa").export_private_key("pkcs8-pem")
    )
    return str(dest_file)


@fixture
def config_entry(hass: HomeAssistant = Depends(hass)) -> MockConfigEntry:
    """Return a default SFTP storage config entry."""
    private_key = _create_private_key_file(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=TEST_AGENT_ID,
        unique_id=TEST_AGENT_ID,
        title=CONFIG_ENTRY_TITLE,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 22,
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
            CONF_PRIVATE_KEY_FILE: str(private_key),
            CONF_BACKUP_LOCATION: "/backup_location",
        },
    )
    entry.runtime_data = SFTPConfigEntryData(**entry.data)
    return entry


@fixture
def mock_ssh_connection() -> Generator[SSHClientConnectionMock]:
    """Mock ``SSHClientConnection`` globally."""
    mock = SSHClientConnectionMock()

    @async_context_manager
    async def mock_connect(*args, **kwargs):
        """Mock ``asyncssh.connect`` to return our mock directly."""
        return mock

    with (
        patch(
            "homeassistant.components.sftp_storage.client.connect",
            side_effect=mock_connect,
        ),
        patch(
            "homeassistant.components.sftp_storage.config_flow.connect",
            side_effect=mock_connect,
        ),
    ):
        yield mock


@fixture
async def setup_integration(
    hass: HomeAssistant = Depends(hass),
    config_entry: MockConfigEntry = Depends(config_entry),
    mock_ssh_connection: SSHClientConnectionMock = Depends(mock_ssh_connection),
) -> AsyncGenerator[SSHClientConnectionMock]:
    """Set up SFTP storage + Backup integrations for testing."""
    config_entry.add_to_hass(hass)
    assert await async_setup_component(hass, BACKUP_DOMAIN, {})
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    yield mock_ssh_connection


# Local copies of hass_client / hass_ws_client wired to our local ``hass``
# fixture (which uses ``tmp_path``). The default fixtures in
# ``tests.hass_fixtures`` are lexically bound to the shared ``hass``
# fixture there, so importing them would yield two independent hass
# instances per test.


@fixture
async def local_auth(hass: HomeAssistant = Depends(hass)):
    """Load the local Home Assistant auth provider against our hass."""
    from homeassistant.auth.providers import homeassistant as ha_auth  # noqa: PLC0415

    prv = ha_auth.HassAuthProvider(
        hass, hass.auth._store, {"type": "homeassistant"}
    )
    await prv.async_initialize()
    hass.auth._providers[(prv.type, prv.id)] = prv
    return prv


@fixture
async def hass_admin_user(
    hass: HomeAssistant = Depends(hass),
    _local_auth: Any = Depends(local_auth),
):
    """Return a Home Assistant admin user bound to our hass."""
    from homeassistant.auth.const import GROUP_ID_ADMIN  # noqa: PLC0415

    admin_group = await hass.auth.async_get_group(GROUP_ID_ADMIN)
    return MockUser(groups=[admin_group]).add_to_hass(hass)


@fixture
async def hass_admin_credential():
    """Provide credentials for the admin user."""
    from homeassistant.auth.models import Credentials  # noqa: PLC0415

    return Credentials(
        id="mock-credential-id",
        auth_provider_type="homeassistant",
        auth_provider_id=None,
        data={"username": "admin"},
        is_new=False,
    )


@fixture
async def hass_access_token(
    hass: HomeAssistant = Depends(hass),
    user=Depends(hass_admin_user),
    credential=Depends(hass_admin_credential),
) -> str:
    """Return an access token for the admin user on our hass."""
    CLIENT_ID = "https://hass.io/"
    await hass.auth.async_link_user(user, credential)
    refresh_token = await hass.auth.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )
    return hass.auth.async_create_access_token(refresh_token)


@fixture
def hass_client(
    hass: HomeAssistant = Depends(hass),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
    hass_access_token: str = Depends(hass_access_token),
) -> ClientSessionGenerator:
    """Return an authenticated HTTP client bound to our hass."""

    async def auth_client(access_token: str | None = hass_access_token):
        return await aiohttp_client(
            hass.http.app, headers={"Authorization": f"Bearer {access_token}"}
        )

    return auth_client


@fixture
def hass_ws_client(
    hass: HomeAssistant = Depends(hass),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
    hass_access_token: str = Depends(hass_access_token),
):
    """Return a WebSocket client bound to our hass."""
    from homeassistant.components.websocket_api.auth import (  # noqa: PLC0415
        TYPE_AUTH,
        TYPE_AUTH_OK,
        TYPE_AUTH_REQUIRED,
    )
    from homeassistant.components.websocket_api.const import URL  # noqa: PLC0415

    async def create_client(
        target_hass: HomeAssistant = hass,
        access_token: str | None = hass_access_token,
    ):
        assert await async_setup_component(target_hass, "websocket_api", {})
        client = await aiohttp_client(target_hass.http.app)
        websocket = await client.ws_connect(URL)
        auth_resp = await websocket.receive_json()
        assert auth_resp["type"] == TYPE_AUTH_REQUIRED

        if access_token is None:
            await websocket.send_json(
                {"type": TYPE_AUTH, "access_token": "incorrect"}
            )
        else:
            await websocket.send_json(
                {"type": TYPE_AUTH, "access_token": access_token}
            )

        auth_ok = await websocket.receive_json()
        assert auth_ok["type"] == TYPE_AUTH_OK

        def _get_next_id() -> Generator[int]:
            i = 0
            while True:
                yield (i := i + 1)

        id_generator = _get_next_id()

        def _send_json_auto_id(data: dict[str, Any]):
            data["id"] = next(id_generator)
            return websocket.send_json(data)

        websocket.client = client  # type: ignore[attr-defined]
        websocket.send_json_auto_id = _send_json_auto_id  # type: ignore[attr-defined]
        return websocket

    return create_client
