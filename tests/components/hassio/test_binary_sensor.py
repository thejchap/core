"""The tests for the hassio binary sensors."""

from dataclasses import replace
from datetime import timedelta
import os
from pathlib import PurePath
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from aiohasupervisor.models import AddonState, InstalledAddonComplete, StoreInfo
from aiohasupervisor.models.mounts import (
    CIFSMountResponse,
    MountsInfo,
    MountState,
    MountType,
    MountUsage,
    NFSMountResponse,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN
from homeassistant.components.hassio.const import DATA_CONFIG_STORE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    addon_changelog,
    addon_installed,
    addon_stats,
    addons_list,
    homeassistant_info,
    homeassistant_stats,
    host_info,
    ingress_panels,
    jobs_info,
    network_info,
    os_info,
    resolution_info,
    store_info,
    supervisor_client,
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
)
from .common import MOCK_REPOSITORIES, MOCK_STORE_ADDONS

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
async def load_hassio_translations(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Load hassio translations so entity_ids use translation_key suffixes."""
    from homeassistant.helpers import translation  # noqa: PLC0415

    await translation.async_load_integrations(hass, {"hassio"})
    # Also pre-cache 'entity' category for hassio
    await translation.async_get_translations(
        hass, hass.config.language, "entity", {"hassio"}
    )


@fixture
def mock_all(
    _translations: None = Depends(load_hassio_translations),
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _addon_stats: AsyncMock = Depends(addon_stats),
    _resolution_info: AsyncMock = Depends(resolution_info),
    _jobs_info: AsyncMock = Depends(jobs_info),
    _host_info: AsyncMock = Depends(host_info),
    _supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    _homeassistant_info: AsyncMock = Depends(homeassistant_info),
    _supervisor_info: AsyncMock = Depends(supervisor_info),
    _addons_list: AsyncMock = Depends(addons_list),
    _network_info: AsyncMock = Depends(network_info),
    _os_info: AsyncMock = Depends(os_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests."""

    def mock_addon_info(slug: str):
        addon = Mock(
            spec=InstalledAddonComplete,
            to_dict=addon_installed.return_value.to_dict,
            **addon_installed.return_value.to_dict(),
        )
        if slug == "test":
            addon.name = "test"
            addon.slug = "test"
            addon.version = "2.0.0"
            addon.version_latest = "2.0.1"
            addon.update_available = True
            addon.state = AddonState.STARTED
            addon.url = "https://github.com/home-assistant/addons/test"
            addon.auto_update = True
        else:
            addon.name = "test2"
            addon.slug = "test2"
            addon.version = "3.1.0"
            addon.version_latest = "3.1.0"
            addon.update_available = False
            addon.state = AddonState.STOPPED
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info


@fixture
def hass_supervisor_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
):
    """Return a websocket client authenticated as the Supervisor user."""

    async def create_client():
        hassio_user_id = hass.data[DATA_CONFIG_STORE].data.hassio_user
        hassio_user = await hass.auth.async_get_user(hassio_user_id)
        assert hassio_user
        assert hassio_user.refresh_tokens
        refresh_token = next(iter(hassio_user.refresh_tokens.values()))
        access_token = hass.auth.async_create_access_token(refresh_token)
        return await hass_ws_client(hass, access_token=access_token)

    return create_client


@test.cases(
    test.case(
        "test_running",
        entity_id="binary_sensor.test_running",
        expected="on",
        addon_state="started",
    ),
    test.case(
        "test2_running",
        entity_id="binary_sensor.test2_running",
        expected="off",
        addon_state="stopped",
    ),
)
async def binary_sensor(
    entity_id: str,
    expected: str,
    addon_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    addon_installed: AsyncMock = Depends(addon_installed),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _mock_all: None = Depends(mock_all),
) -> None:
    """Test hassio OS and addons binary sensor."""
    supervisor_client.store.info.return_value = StoreInfo(
        addons=MOCK_STORE_ADDONS, repositories=MOCK_REPOSITORIES
    )

    addon_installed.return_value.state = addon_state
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id)).to_be_none()

    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(expected)


@test
async def mount_binary_sensor(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _mock_all: None = Depends(mock_all),
) -> None:
    """Test hassio mounts binary sensor."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be_truthy()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.nas_connected"

    expect(hass.states.get(entity_id)).to_be_none()

    mock_mounts: list[CIFSMountResponse | NFSMountResponse] = [
        CIFSMountResponse(
            share="files",
            server="1.2.3.4",
            name="NAS",
            type=MountType.CIFS,
            usage=MountUsage.SHARE,
            read_only=False,
            state=MountState.ACTIVE,
            user_path=PurePath("/share/nas"),
        )
    ]
    supervisor_client.mounts.info = AsyncMock(
        return_value=MountsInfo(default_backup_mount=None, mounts=mock_mounts)
    )

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1000))
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.get(entity_id)).to_be_none()

    import sys
    from homeassistant.helpers import translation
    bin_entities = [e for e in entity_registry.entities.keys() if 'binary' in e]
    print(f"BINARY entities: {bin_entities}", file=sys.stderr)
    cache = translation._async_get_translations_cache(hass)
    print(f"Cache lang: {hass.config.language}", file=sys.stderr)
    print(f"Loaded: {cache.cache_data.loaded}", file=sys.stderr)
    print(f"Cache keys: {list(cache.cache_data.cache.get(hass.config.language, {}).get('entity', {}).keys())[:20]}", file=sys.stderr)
    print(f"Hassio entity translations: {[k for k in cache.cache_data.cache.get(hass.config.language, {}).get('entity', {}).keys() if 'hassio' in k]}", file=sys.stderr)
    print(f"Sample entity name: {[entity_registry.entities[e].translation_key for e in bin_entities]}", file=sys.stderr)
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get(entity_id)
    expect(entity).not_to_be_none()
    expect(entity.state).to_equal("on")

    mock_mounts[0] = replace(mock_mounts[0], state=MountState.FAILED)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1000))
    await hass.async_block_till_done(wait_background_tasks=True)
    entity = hass.states.get(entity_id)
    expect(entity).not_to_be_none()
    expect(entity.state).to_equal("off")

    mount = mock_mounts.pop()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1000))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(hass.states.get(entity_id)).to_be_none()

    mock_mounts.append(mount)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1000))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(hass.states.get(entity_id)).not_to_be_none()


@test
async def mount_refresh_after_issue(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    _mock_all: None = Depends(mock_all),
) -> None:
    """Test hassio mount state is refreshed after an issue was send by the supervisor."""
    mock_mounts: list[CIFSMountResponse | NFSMountResponse] = [
        CIFSMountResponse(
            share="files",
            server="1.2.3.4",
            name="NAS",
            type=MountType.CIFS,
            usage=MountUsage.SHARE,
            read_only=False,
            state=MountState.ACTIVE,
            user_path=PurePath("/share/nas"),
        )
    ]
    supervisor_client.mounts.info = AsyncMock(
        return_value=MountsInfo(default_backup_mount=None, mounts=mock_mounts)
    )

    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be_truthy()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.nas_connected"
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get(entity_id)
    expect(entity).not_to_be_none()
    expect(entity.state).to_equal("on")

    mock_mounts[0] = replace(mock_mounts[0], state=MountState.FAILED)
    client = await hass_supervisor_ws_client()
    issue_uuid = uuid4().hex
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "mount_failed",
                    "context": "mount",
                    "reference": "nas",
                    "suggestions": [
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_reload",
                            "context": "mount",
                            "reference": "nas",
                        },
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_remove",
                            "context": "mount",
                            "reference": "nas",
                        },
                    ],
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)
    entity = hass.states.get(entity_id)
    expect(entity).not_to_be_none()
    expect(entity.state).to_equal("off")

    mock_mounts[0] = replace(mock_mounts[0], state=MountState.ACTIVE)
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "issue_removed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "mount_failed",
                    "context": "mount",
                    "reference": "nas",
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done(wait_background_tasks=True)
    entity = hass.states.get(entity_id)
    expect(entity).not_to_be_none()
    expect(entity.state).to_equal("on")
