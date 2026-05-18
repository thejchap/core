"""Test the UniFi Protect setup flow."""

from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test
from uiprotect import NvrError, ProtectApiClient
from uiprotect.api import DEVICE_UPDATE_INTERVAL
from uiprotect.data import NVR, Bootstrap, CloudAccount, Light
from uiprotect.exceptions import BadRequest, NotAuthorized

from homeassistant.components.unifiprotect.const import (
    AUTH_RETRIES,
    CONF_ALLOW_EA,
    DOMAIN,
)
from homeassistant.components.unifiprotect.data import (
    async_ufp_instance_for_config_entry_ids,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from . import _patch_discovery
from ._fixtures import (
    bootstrap as bootstrap_fx,
    cloud_account as cloud_account_fx,
    light as light_fx,
    old_nvr as old_nvr_fx,
    ufp as ufp_fx,
    ufp_client as ufp_client_fx,
    ufp_config_entry as ufp_config_entry_fx,
)
from .utils import MockUFPFixture, init_entry, time_changed

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Module-level anchor for tryke's executor."""
    return 0


@test.skip("uses syrupy snapshot")
async def setup_creates_nvr_device() -> None:
    """Stub for test_setup_creates_nvr_device (snapshot-based)."""


@test
async def setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test working setup of unifiprotect entry."""
    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)
    expect(ufp.api.update.called).to_be_truthy()
    expect(ufp.entry.unique_id).to_equal(ufp.api.bootstrap.nvr.mac)


@test
async def setup_multiple(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
    bootstrap: Bootstrap = Depends(bootstrap_fx),
) -> None:
    """Test working setup of unifiprotect entry."""
    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)
    expect(ufp.api.update.called).to_be_truthy()
    expect(ufp.entry.unique_id).to_equal(ufp.api.bootstrap.nvr.mac)

    nvr = bootstrap.nvr
    nvr._api = ufp.api
    nvr.mac = "A1E00C826983"
    ufp.api.get_nvr = AsyncMock(return_value=nvr)

    with patch(
        "homeassistant.components.unifiprotect.utils.ProtectApiClient"
    ) as mock_api:
        mock_config = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                CONF_API_KEY: "test-api-key",
                "id": "UnifiProtect",
                "port": 443,
                "verify_ssl": False,
            },
            version=2,
        )
        mock_config.add_to_hass(hass)

        mock_api.return_value = ufp.api

        await hass.config_entries.async_setup(mock_config.entry_id)
        await hass.async_block_till_done()

        expect(mock_config.state).to_be(ConfigEntryState.LOADED)
        expect(ufp.api.update.called).to_be_truthy()
        expect(mock_config.unique_id).to_equal(ufp.api.bootstrap.nvr.mac)


@test
async def unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
    light: Light = Depends(light_fx),
) -> None:
    """Test unloading of unifiprotect entry."""
    await init_entry(hass, ufp, [light])
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(ufp.entry.entry_id)
    expect(ufp.entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(ufp.api.async_disconnect_ws.called).to_be_truthy()


@test
async def remove_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test removal of unifiprotect entry clears session."""
    await init_entry(hass, ufp, [])
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    ufp.api.clear_session = AsyncMock()

    await hass.config_entries.async_remove(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.api.clear_session.called).to_be_truthy()


@test
async def remove_entry_not_loaded(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test removal of unloaded unifiprotect entry still clears session."""
    ufp.entry.add_to_hass(hass)
    ufp.api.clear_session = AsyncMock()

    with patch(
        "homeassistant.components.unifiprotect.async_create_api_client",
        return_value=ufp.api,
    ):
        await hass.config_entries.async_remove(ufp.entry.entry_id)
        await hass.async_block_till_done()

    expect(ufp.api.clear_session.called).to_be_truthy()


@test
async def remove_entry_clear_session_fails(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test removal succeeds even when clear_session fails."""
    await init_entry(hass, ufp, [])
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    ufp.api.clear_session = AsyncMock(side_effect=PermissionError("Permission denied"))

    await hass.config_entries.async_remove(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.api.clear_session.called).to_be_truthy()


@test
async def remove_entry_not_loaded_clear_session_fails(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test removal succeeds when not loaded and clear_session fails."""
    ufp.entry.add_to_hass(hass)
    expect(ufp.entry.state is ConfigEntryState.LOADED).to_be_falsy()

    with patch(
        "homeassistant.components.unifiprotect.async_create_api_client"
    ) as mock_create:
        mock_api = Mock(spec=ProtectApiClient)
        mock_api.clear_session = AsyncMock(side_effect=OSError("Read-only file system"))
        mock_create.return_value = mock_api

        await hass.config_entries.async_remove(ufp.entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_api.clear_session.called).to_be_truthy()


@test
async def setup_too_old(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
    old_nvr: NVR = Depends(old_nvr_fx),
) -> None:
    """Test setup of unifiprotect entry with too old of version of UniFi Protect."""
    old_bootstrap = ufp.api.bootstrap.model_copy()
    old_bootstrap.nvr = old_nvr
    ufp.api.update.return_value = old_bootstrap
    ufp.api.bootstrap = old_bootstrap

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_cloud_account(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
    cloud_account: CloudAccount = Depends(cloud_account_fx),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test setup of unifiprotect entry with cloud account."""
    bootstrap = ufp.api.bootstrap
    user = bootstrap.users[bootstrap.auth_user_id]
    user.cloud_account = cloud_account
    bootstrap.users[bootstrap.auth_user_id] = user
    ufp.api.get_bootstrap.return_value = bootstrap
    ws_client = await hass_ws_client(hass)

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(len(msg["result"]["issues"]) > 0).to_be_truthy()
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "cloud_user":
            issue = i
    expect(issue is not None).to_be_truthy()


@test
async def setup_failed_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test setup of unifiprotect entry with failed update."""
    ufp.api.update = AsyncMock(side_effect=NvrError)

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(ufp.api.update.called).to_be_truthy()


@test
async def setup_failed_update_reauth(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test setup of unifiprotect entry with update that gives unauthroized error."""
    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    # reauth should not be triggered until there are 10 auth failures in a row
    # to verify it is not transient
    ufp.api.update = AsyncMock(side_effect=NotAuthorized)
    for _ in range(AUTH_RETRIES):
        await time_changed(hass, DEVICE_UPDATE_INTERVAL)
        expect(len(hass.config_entries.flow._progress)).to_equal(0)

    expect(ufp.api.update.call_count).to_equal(AUTH_RETRIES)
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    await time_changed(hass, DEVICE_UPDATE_INTERVAL)
    expect(ufp.api.update.call_count).to_equal(AUTH_RETRIES + 1)
    expect(len(hass.config_entries.flow._progress)).to_equal(1)


@test
async def setup_failed_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test setup of unifiprotect entry with generic error."""
    ufp.api.update = AsyncMock(side_effect=NvrError)

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_failed_auth(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test setup of unifiprotect entry with unauthorized error after multiple retries."""
    ufp.api.update = AsyncMock(side_effect=NotAuthorized)

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    for _ in range(AUTH_RETRIES - 1):
        await hass.config_entries.async_reload(ufp.entry.entry_id)
        expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_RETRY)

    await hass.config_entries.async_reload(ufp.entry.entry_id)
    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_starts_discovery(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_config_entry: MockConfigEntry = Depends(ufp_config_entry_fx),
    ufp_client=Depends(ufp_client_fx),
) -> None:
    """Test setting up will start discovery via unifi_discovery dependency."""
    with (
        _patch_discovery(),
        patch(
            "homeassistant.components.unifiprotect.utils.ProtectApiClient"
        ) as mock_api,
    ):
        ufp_config_entry.add_to_hass(hass)
        mock_api.return_value = ufp_client
        ufp = MockUFPFixture(ufp_config_entry, ufp_client)

        await hass.config_entries.async_setup(ufp.entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)
        # Discovery is now handled by unifi_discovery dependency
        expect(
            len(hass.config_entries.flow.async_progress_by_handler(DOMAIN))
        ).to_equal(1)


@test
async def device_remove_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
    light: Light = Depends(light_fx),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test we can only remove a device that no longer exists."""
    await init_entry(hass, ufp, [light])
    expect(await async_setup_component(hass, "config", {})).to_be_truthy()
    entity_id = "light.test_light"
    entry_id = ufp.entry.entry_id

    entity = entity_registry.async_get(entity_id)
    expect(entity is not None).to_be_truthy()

    live_device_entry = device_registry.async_get(entity.device_id)
    client = await hass_ws_client(hass)
    response = await client.remove_device(live_device_entry.id, entry_id)
    expect(response["success"]).to_be_falsy()

    dead_device_entry = device_registry.async_get_or_create(
        config_entry_id=entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "e9:88:e7:b8:b4:40")},
    )
    response = await client.remove_device(dead_device_entry.id, entry_id)
    expect(response["success"]).to_be_truthy()


@test
async def device_remove_devices_nvr(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test we can only remove a NVR device that no longer exists."""
    expect(await async_setup_component(hass, "config", {})).to_be_truthy()

    ufp.api.get_bootstrap = AsyncMock(return_value=ufp.api.bootstrap)
    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()
    entry_id = ufp.entry.entry_id

    live_device_entry = list(device_registry.devices.values())[0]
    client = await hass_ws_client(hass)
    response = await client.remove_device(live_device_entry.id, entry_id)
    expect(response["success"]).to_be_falsy()


@test.cases(
    test.case("one_matching_domain", scenario="match"),
    test.case("no_matching_domain", scenario="no_match"),
)
async def async_ufp_instance_for_config_entry_ids_test(
    scenario: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test async_ufp_instance_for_config_entry_ids with various entry configurations."""
    if scenario == "match":
        mock_entries = [
            MockConfigEntry(domain=DOMAIN, entry_id="1", data={}),
            MockConfigEntry(domain="other_domain", entry_id="2", data={}),
        ]
        expected_result: str | None = "mock_api_instance_1"
    else:
        mock_entries = [
            MockConfigEntry(domain="other_domain", entry_id="1", data={}),
            MockConfigEntry(domain="other_domain", entry_id="2", data={}),
        ]
        expected_result = None

    for index, entry in enumerate(mock_entries):
        entry.add_to_hass(hass)
        entry.runtime_data = Mock(api=f"mock_api_instance_{index + 1}")

    entry_ids = {entry.entry_id for entry in mock_entries}

    result = async_ufp_instance_for_config_entry_ids(hass, entry_ids)

    expect(result).to_equal(expected_result)


@test
async def setup_creates_api_key_when_missing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test that API key is created when missing and user has write permissions."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=True))

    ufp.api.is_api_key_set.return_value = False
    ufp.api.create_api_key = AsyncMock(return_value="new-api-key-123")

    def set_api_key_side_effect(key):
        ufp.api.is_api_key_set.return_value = True

    ufp.api.set_api_key.side_effect = set_api_key_side_effect

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    ufp.api.create_api_key.assert_called_once_with(name="Home Assistant (test home)")
    ufp.api.set_api_key.assert_called_once_with("new-api-key-123")

    expect(ufp.entry.data[CONF_API_KEY]).to_equal("new-api-key-123")
    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)


@test
async def setup_skips_api_key_creation_when_no_write_permission(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test that API key creation is skipped when user has no write permissions."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=False))

    ufp.api.is_api_key_set.return_value = False

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    ufp.api.create_api_key.assert_not_called()
    ufp.api.set_api_key.assert_not_called()


@test
async def setup_handles_api_key_creation_failure(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test handling of API key creation failure."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=True))

    ufp.api.is_api_key_set.return_value = False
    ufp.api.create_api_key = AsyncMock(
        side_effect=NotAuthorized("Failed to create API key")
    )

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    ufp.api.create_api_key.assert_called_once_with(name="Home Assistant (test home)")
    ufp.api.set_api_key.assert_not_called()


@test
async def setup_handles_api_key_creation_bad_request(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test handling of API key creation BadRequest error."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=True))

    ufp.api.is_api_key_set.return_value = False
    ufp.api.create_api_key = AsyncMock(
        side_effect=BadRequest("Invalid API key creation request")
    )

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    ufp.api.create_api_key.assert_called_once_with(name="Home Assistant (test home)")
    ufp.api.set_api_key.assert_not_called()


@test
async def setup_with_existing_api_key(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test setup when API key is already set."""
    ufp.api.is_api_key_set.return_value = True

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.LOADED)

    ufp.api.create_api_key.assert_not_called()
    ufp.api.set_api_key.assert_not_called()


@test
async def setup_api_key_creation_returns_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test handling when API key creation returns None."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=True))

    ufp.api.is_api_key_set.return_value = False
    ufp.api.create_api_key = AsyncMock(return_value=None)

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    ufp.api.create_api_key.assert_called_once_with(name="Home Assistant (test home)")
    ufp.api.set_api_key.assert_called_once_with(None)


@test
async def migrate_entry_version_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test remove CONF_ALLOW_EA from options while migrating a 1 config entry to 2."""
    with patch(
        "homeassistant.components.unifiprotect.async_setup_entry", return_value=True
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"test": "1", "test2": "2", CONF_ALLOW_EA: "True"},
            version=1,
            unique_id="123456",
        )
        entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
        expect(entry.version).to_equal(2)
        expect(entry.options.get(CONF_ALLOW_EA)).to_be(None)
        expect(entry.unique_id).to_equal("123456")


@test
async def setup_skips_api_key_creation_when_no_auth_user(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test that API key creation is skipped when auth_user is None."""
    ufp.api.is_api_key_set.return_value = False

    with patch.dict(ufp.api.bootstrap.users, {}, clear=True):
        await hass.config_entries.async_setup(ufp.entry.entry_id)
        await hass.async_block_till_done()

        expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

        ufp.api.create_api_key.assert_not_called()
        ufp.api.set_api_key.assert_not_called()


@test
async def setup_fails_when_api_key_still_missing_after_creation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test that setup fails when API key is still missing after creation attempts."""
    object.__setattr__(ufp.api.bootstrap.nvr, "can_write", Mock(return_value=True))

    ufp.api.is_api_key_set.return_value = False
    ufp.api.create_api_key = AsyncMock(return_value="new-api-key-123")
    ufp.api.set_api_key = Mock()

    await hass.config_entries.async_setup(ufp.entry.entry_id)
    await hass.async_block_till_done()

    expect(ufp.entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    ufp.api.create_api_key.assert_called_once_with(name="Home Assistant (test home)")
    ufp.api.set_api_key.assert_called_once_with("new-api-key-123")
