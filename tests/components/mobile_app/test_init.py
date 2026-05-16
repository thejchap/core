"""Tests for the mobile app integration."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import Mock, patch

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud import CloudNotAvailable
from homeassistant.components.mobile_app.const import (
    ATTR_DEVICE_NAME,
    CONF_CLOUDHOOK_URL,
    CONF_USER_ID,
    DATA_DELETED_IDS,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import create_registrations as create_registrations_fixture, webhook_client as webhook_client_fixture

from .const import CALL_SERVICE, REGISTER_CLEARTEXT

from tests.common import (
    MockConfigEntry,
    MockUser,
    async_mock_cloud_connection_status,
    async_mock_service,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
async def unload_unloads(
    _trigger: int = Depends(_trigger_executor),
    _registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(create_registrations_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test we clean up when we unload."""
    # Second config entry is the one without encryption
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    webhook_id = config_entry.data["webhook_id"]
    calls = async_mock_service(hass, "test", "mobile_app")

    # Test it works
    await webhook_client.post(f"/api/webhook/{webhook_id}", json=CALL_SERVICE)
    expect(len(calls)).to_equal(1)

    await hass.config_entries.async_unload(config_entry.entry_id)

    # Test it no longer works
    await webhook_client.post(f"/api/webhook/{webhook_id}", json=CALL_SERVICE)
    expect(len(calls)).to_equal(1)


@test
async def remove_entry(
    _trigger: int = Depends(_trigger_executor),
    _registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(create_registrations_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we clean up when we remove entry."""
    for config_entry in hass.config_entries.async_entries("mobile_app"):
        await hass.config_entries.async_remove(config_entry.entry_id)
        expect(config_entry.data["webhook_id"] in hass.data[DOMAIN][DATA_DELETED_IDS]).to_be(True)

    expect(len(device_registry.devices)).to_equal(0)
    expect(len(entity_registry.entities)).to_equal(0)


async def _run_create_cloud_hook(
    hass: HomeAssistant,
    hass_admin_user: MockUser,
    additional_config: dict[str, Any],
    async_active_subscription_return_value: bool,
    additional_steps: Callable[
        [ConfigEntry, Mock, str, Callable[[Any], None]], Awaitable[None]
    ],
) -> None:
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            **additional_config,
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    cloudhook_change_callback = None

    def mock_listen_cloudhook_change(
        _: HomeAssistant, _webhook_id: str, callback: Callable[[Any], None]
    ):
        """Mock the cloudhook change listener."""
        nonlocal cloudhook_change_callback
        cloudhook_change_callback = callback
        return lambda: None  # Return unsubscribe function

    cloud_hook = "https://hook-url"

    async def mock_get_or_create_cloudhook(_hass: HomeAssistant, _webhook_id: str):
        """Mock creating a cloudhook and trigger the change callback."""
        assert cloudhook_change_callback is not None
        cloudhook_change_callback({CONF_CLOUDHOOK_URL: cloud_hook})
        return cloud_hook

    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=async_active_subscription_return_value,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=True),
        patch(
            "homeassistant.components.cloud.async_get_or_create_cloudhook",
            side_effect=mock_get_or_create_cloudhook,
        ) as mock_async_get_or_create_cloudhook,
        patch(
            "homeassistant.components.cloud.async_listen_cloudhook_change",
            side_effect=mock_listen_cloudhook_change,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        expect(cloudhook_change_callback is not None).to_be(True)

        await additional_steps(
            config_entry,
            mock_async_get_or_create_cloudhook,
            cloud_hook,
            cloudhook_change_callback,
        )


@test
async def create_cloud_hook_on_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test creating a cloud hook during setup."""

    async def additional_steps(
        config_entry: ConfigEntry,
        mock_create_cloudhook: Mock,
        cloud_hook: str,
        cloudhook_change_callback: Callable[[Any], None],
    ) -> None:
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(cloud_hook)
        mock_create_cloudhook.assert_called_once_with(
            hass, config_entry.data[CONF_WEBHOOK_ID]
        )

    await _run_create_cloud_hook(hass, hass_admin_user, {}, True, additional_steps)


@test.cases(
    test.case("CloudNotAvailable", exception=CloudNotAvailable),
    test.case("ValueError", exception=ValueError),
)
async def remove_cloudhook(
    exception: type[Exception],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test removing a cloud hook when config entry is removed."""

    async def additional_steps(
        config_entry: ConfigEntry,
        mock_create_cloudhook: Mock,
        cloud_hook: str,
        cloudhook_change_callback: Callable[[Any], None],
    ) -> None:
        webhook_id = config_entry.data[CONF_WEBHOOK_ID]
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(cloud_hook)
        with patch(
            "homeassistant.components.cloud.async_delete_cloudhook",
            side_effect=exception,
        ) as delete_cloudhook:
            await hass.config_entries.async_remove(config_entry.entry_id)
            await hass.async_block_till_done()
            delete_cloudhook.assert_called_once_with(hass, webhook_id)
            expect(str(exception) not in caplog.text).to_be(True)

    await _run_create_cloud_hook(hass, hass_admin_user, {}, True, additional_steps)


@test
async def create_cloud_hook_aleady_exists(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test creating a cloud hook is not called, when a cloud hook already exists."""
    cloud_hook = "https://hook-url-already-exists"

    async def additional_steps(
        config_entry: ConfigEntry,
        mock_create_cloudhook: Mock,
        _: str,
        cloudhook_change_callback: Callable[[Any], None],
    ) -> None:
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(cloud_hook)
        mock_create_cloudhook.assert_not_called()

    await _run_create_cloud_hook(
        hass, hass_admin_user, {CONF_CLOUDHOOK_URL: cloud_hook}, True, additional_steps
    )


@test
async def create_cloud_hook_after_connection(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test creating a cloud hook when connected to the cloud."""

    async def additional_steps(
        config_entry: ConfigEntry,
        mock_create_cloudhook: Mock,
        cloud_hook: str,
        cloudhook_change_callback: Callable[[Any], None],
    ) -> None:
        expect(CONF_CLOUDHOOK_URL not in config_entry.data).to_be(True)
        mock_create_cloudhook.assert_not_called()

        async_mock_cloud_connection_status(hass, True)
        await hass.async_block_till_done()

        # Simulate cloudhook creation by calling the callback
        cloudhook_change_callback({CONF_CLOUDHOOK_URL: cloud_hook})
        await hass.async_block_till_done()

        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(cloud_hook)
        mock_create_cloudhook.assert_called_once_with(
            hass, config_entry.data[CONF_WEBHOOK_ID]
        )

    await _run_create_cloud_hook(hass, hass_admin_user, {}, False, additional_steps)


@test.cases(
    test.case("logged_in", cloud_logged_in=True, should_cloudhook_exist=True),
    test.case("logged_out", cloud_logged_in=False, should_cloudhook_exist=False),
)
async def delete_cloud_hook(
    cloud_logged_in: bool,
    should_cloudhook_exist: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test deleting the cloud hook only when logged out of the cloud."""

    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hook-url-already-exists",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.cloud.async_is_logged_in",
            return_value=cloud_logged_in,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        expect((CONF_CLOUDHOOK_URL in config_entry.data) == should_cloudhook_exist).to_be(True)


@test
async def setup_entry_local_only_user_no_cloudhook(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that cloudhook is not created for local_only users during setup."""
    hass_admin_user.local_only = True

    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=True),
        patch(
            "homeassistant.components.cloud.async_get_or_create_cloudhook",
        ) as mock_create_cloudhook,
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        # Cloudhook should not be created for local_only user
        expect(CONF_CLOUDHOOK_URL not in config_entry.data).to_be(True)
        mock_create_cloudhook.assert_not_called()


@test
async def setup_entry_local_only_user_cleans_existing_cloudhook(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that existing cloudhook is cleaned up for local_only users during setup."""
    hass_admin_user.local_only = True

    webhook_id = "test-webhook-id"
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hooks.nabu.casa/stale",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch(
            "homeassistant.components.cloud.async_delete_cloudhook",
        ) as delete_cloudhook,
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    # Existing cloudhook should be removed for local_only user
    expect(CONF_CLOUDHOOK_URL not in config_entry.data).to_be(True)
    delete_cloudhook.assert_called_once_with(hass, webhook_id)


@test
async def remove_entry_on_user_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test removing related config entry, when a user gets removed from HA."""

    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hook-url-already-exists",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    await hass.auth.async_remove_user(hass_admin_user)
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(0)


@test
async def cloudhook_cleanup_on_disconnect_and_logout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test cloudhook is cleaned up when cloud disconnects and user is logged out."""
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hook-url",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.cloud.async_is_logged_in",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_is_connected",
            return_value=True,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        # Cloudhook should still exist
        expect(CONF_CLOUDHOOK_URL in config_entry.data).to_be(True)

    # Simulate cloud disconnect and logout
    with patch(
        "homeassistant.components.cloud.async_is_logged_in",
        return_value=False,
    ):
        async_mock_cloud_connection_status(hass, False)
        await hass.async_block_till_done()

        # Cloudhook should be removed from config entry
        expect(CONF_CLOUDHOOK_URL not in config_entry.data).to_be(True)


@test
async def cloudhook_persists_on_disconnect_when_logged_in(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test cloudhook persists when cloud disconnects but user is still logged in."""
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: "test-webhook-id",
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hook-url",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.cloud.async_is_logged_in",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_is_connected",
            return_value=True,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        # Cloudhook should exist
        expect(CONF_CLOUDHOOK_URL in config_entry.data).to_be(True)

        # Simulate cloud disconnect while still logged in
        async_mock_cloud_connection_status(hass, False)
        await hass.async_block_till_done()

        # Cloudhook should still exist because user is still logged in
        expect(CONF_CLOUDHOOK_URL in config_entry.data).to_be(True)


@test
async def cloudhook_change_listener_deletion(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test cloudhook change listener removes cloudhook from config entry on deletion."""
    webhook_id = "test-webhook-id"
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: "https://hook-url",
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    cloudhook_change_callback = None

    def mock_listen_cloudhook_change(
        _: HomeAssistant, _webhook_id: str, callback: Callable[[Any], None]
    ):
        """Mock the cloudhook change listener."""
        nonlocal cloudhook_change_callback
        cloudhook_change_callback = callback
        return lambda: None  # Return unsubscribe function

    with (
        patch(
            "homeassistant.components.cloud.async_is_logged_in",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_is_connected",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_listen_cloudhook_change",
            side_effect=mock_listen_cloudhook_change,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        # Cloudhook should exist
        expect(CONF_CLOUDHOOK_URL in config_entry.data).to_be(True)
        # Change listener should have been registered
        expect(cloudhook_change_callback is not None).to_be(True)

        # Simulate cloudhook deletion by calling the callback with None
        cloudhook_change_callback(None)
        await hass.async_block_till_done()

        # Cloudhook should be removed from config entry
        expect(CONF_CLOUDHOOK_URL not in config_entry.data).to_be(True)


@test
async def cloudhook_change_listener_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test cloudhook change listener updates cloudhook URL in config entry."""
    webhook_id = "test-webhook-id"
    original_url = "https://hook-url"
    config_entry = MockConfigEntry(
        data={
            **REGISTER_CLEARTEXT,
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_DEVICE_NAME: "Test",
            ATTR_DEVICE_ID: "Test",
            CONF_USER_ID: hass_admin_user.id,
            CONF_CLOUDHOOK_URL: original_url,
        },
        domain=DOMAIN,
        title="Test",
    )
    config_entry.add_to_hass(hass)

    cloudhook_change_callback = None

    def mock_listen_cloudhook_change(hass_instance, wh_id: str, callback):
        """Mock the cloudhook change listener."""
        nonlocal cloudhook_change_callback
        cloudhook_change_callback = callback
        return lambda: None  # Return unsubscribe function

    with (
        patch(
            "homeassistant.components.cloud.async_is_logged_in",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_is_connected",
            return_value=True,
        ),
        patch(
            "homeassistant.components.cloud.async_listen_cloudhook_change",
            side_effect=mock_listen_cloudhook_change,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)
        # Cloudhook should exist with original URL
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(original_url)
        # Change listener should have been registered
        expect(cloudhook_change_callback is not None).to_be(True)

        # Simulate cloudhook URL change
        new_url = "https://new-hook-url"
        cloudhook_change_callback({CONF_CLOUDHOOK_URL: new_url})
        await hass.async_block_till_done()

        # Cloudhook URL should be updated in config entry
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(new_url)

        # Simulate same URL update (should not trigger update)
        cloudhook_change_callback({CONF_CLOUDHOOK_URL: new_url})
        await hass.async_block_till_done()

        # URL should remain the same
        expect(config_entry.data[CONF_CLOUDHOOK_URL]).to_equal(new_url)
