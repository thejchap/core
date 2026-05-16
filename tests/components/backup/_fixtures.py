"""Tryke fixtures for the Backup integration."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from pathlib import Path
import shutil
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.backup import DOMAIN
from homeassistant.config_entries import ConfigEntryState
import homeassistant.core as ha
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame, translation as translation_helper
from homeassistant.util.async_ import create_eager_task

from tests.common import MockUser, async_test_home_assistant, get_fixture_path
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aiohttp_client as aiohttp_client_fx,
    hass_storage as hass_storage_fx,
    load_registries as load_registries_fx,
    tmp_path as tmp_path_fx,
)

type ComponentSetup = Callable[[], Awaitable[None]]


@fixture
def available_backups() -> list[Path]:
    """Default: no preinstalled backup files in the config dir."""
    return []


@fixture
def hass_config_dir(
    tmp_path: Path = Depends(tmp_path_fx),
    available_backups: list[Path] = Depends(available_backups),
) -> str:
    """Create a temporary hass config dir populated with backup fixtures."""
    shutil.copytree(
        get_fixture_path("config_dir_contents", DOMAIN),
        tmp_path,
        symlinks=True,
        dirs_exist_ok=True,
    )
    for backup in available_backups:
        (get_fixture_path("test_backups", DOMAIN) / backup).copy_into(
            tmp_path / "backups"
        )
    return tmp_path.as_posix()


@fixture
def _patch_instance_id() -> Generator[None]:
    """Mock the instance id used in backup metadata."""
    with patch(
        "homeassistant.components.backup.manager.instance_id.async_get",
        return_value="our_uuid",
    ):
        yield


@fixture
async def hass(
    load_registries: bool = Depends(load_registries_fx),
    hass_config_dir: str = Depends(hass_config_dir),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    _instance_id: None = Depends(_patch_instance_id),
) -> AsyncGenerator[HomeAssistant]:
    """Provide a hass instance using the backup-specific config dir."""
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


@fixture
def mock_backups() -> Generator[None]:
    """Redirect ``CoreLocalBackupAgent`` to read from the test_backups dir."""
    from homeassistant.components.backup import backup as core_backup  # noqa: PLC0415

    class CoreLocalBackupAgent(core_backup.CoreLocalBackupAgent):
        def __init__(self, hass: HomeAssistant) -> None:
            super().__init__(hass)
            self._backup_dir = get_fixture_path("test_backups", DOMAIN)

    with patch.object(core_backup, "CoreLocalBackupAgent", CoreLocalBackupAgent):
        yield


# ---------------------------------------------------------------------------
# Auth + HTTP client fixtures bound to our local ``hass``.
# ---------------------------------------------------------------------------


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
) -> MockUser:
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
    user: MockUser = Depends(hass_admin_user),
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
