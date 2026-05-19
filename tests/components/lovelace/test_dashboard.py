"""Test the Lovelace initialization."""

import time
from typing import Any
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import frontend
from homeassistant.components.lovelace import const, dashboard
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component

from ._fixtures import mock_onboarding_done as mock_onboarding_done_fx

from tests.common import assert_setup_component, async_capture_events
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def lovelace_from_storage_new_installation(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test new installation has default lovelace panel but no dashboard entry."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Default lovelace panel is registered for backward compatibility
    expect("lovelace" in hass.data[frontend.DATA_PANELS]).to_be(True)

    client = await hass_ws_client(hass)

    # Dashboards list should be empty (no dashboard entry created)
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])


@test
async def lovelace_from_storage_migration(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we migrate existing lovelace config from storage to dashboard."""
    # Pre-populate storage with existing lovelace config
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }

    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # After migration, lovelace panel should be registered as a dashboard
    expect("lovelace" in hass.data[frontend.DATA_PANELS]).to_be(True)
    expect(hass.data[frontend.DATA_PANELS]["lovelace"].config).to_equal(
        {"mode": "storage"}
    )

    client = await hass_ws_client(hass)

    # Dashboard should be in the list
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(1)
    expect(response["result"][0]["url_path"]).to_equal("lovelace")
    expect(response["result"][0]["title"]).to_equal("Overview")

    # Fetch migrated config
    await client.send_json({"id": 6, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"views": [{"title": "Home"}]})

    # Old storage key should be gone, new one should exist
    expect(dashboard.CONFIG_STORAGE_KEY_DEFAULT in hass_storage).to_be(False)
    expect(dashboard.CONFIG_STORAGE_KEY.format("lovelace") in hass_storage).to_be(True)

    # Store new config
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {
            "id": 7,
            "type": "lovelace/config/save",
            "url_path": "lovelace",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(
        hass_storage[dashboard.CONFIG_STORAGE_KEY.format("lovelace")]["data"]
    ).to_equal({"config": {"yo": "hello"}})
    expect(len(events)).to_equal(1)

    # Load new config
    await client.send_json({"id": 8, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"yo": "hello"})

    # Test with recovery mode
    hass.config.recovery_mode = True
    await client.send_json({"id": 9, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    expect(response["success"]).to_be(False)
    expect(response["error"]["code"]).to_equal("config_not_found")

    await client.send_json(
        {
            "id": 10,
            "type": "lovelace/config/save",
            "url_path": "lovelace",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    await client.send_json(
        {"id": 11, "type": "lovelace/config/delete", "url_path": "lovelace"}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)


@test
async def lovelace_dashboard_deleted_re_registers_panel(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test deleting the lovelace dashboard re-registers the default panel."""
    # Pre-populate storage with existing lovelace config (triggers migration)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }

    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # After migration, lovelace panel should be registered as a dashboard
    expect("lovelace" in hass.data[frontend.DATA_PANELS]).to_be(True)

    client = await hass_ws_client(hass)

    # Dashboard should be in the list
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(1)
    dashboard_id = response["result"][0]["id"]

    # Delete the lovelace dashboard
    await client.send_json(
        {"id": 6, "type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    # Dashboard should be gone from the list
    await client.send_json({"id": 7, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])

    # But the lovelace panel should still be registered (re-registered as default)
    expect("lovelace" in hass.data[frontend.DATA_PANELS]).to_be(True)


@test
async def lovelace_migration_completes_when_both_files_exist(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test migration completes when both old and new storage files exist."""
    # Pre-populate both old and new storage (simulating incomplete migration)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Old"}]}},
    }
    hass_storage[dashboard.CONFIG_STORAGE_KEY.format("lovelace")] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY.format("lovelace"),
        "data": {"config": {"views": [{"title": "New"}]}},
    }

    with patch("homeassistant.components.lovelace.os.rename") as mock_rename:
        expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Old file should be renamed as backup
    old_path = hass.config.path(".storage", dashboard.CONFIG_STORAGE_KEY_DEFAULT)
    mock_rename.assert_called_once_with(old_path, old_path + "_old")

    # Dashboard should be created, completing the incomplete migration
    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(1)
    expect(response["result"][0]["url_path"]).to_equal("lovelace")

    # New storage data should be preserved (not overwritten with old data)
    await client.send_json({"id": 6, "type": "lovelace/config", "url_path": "lovelace"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"views": [{"title": "New"}]})


@test
async def lovelace_migration_skipped_when_already_migrated(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test migration is skipped when dashboard already exists."""
    # Pre-populate dashboards with existing lovelace dashboard
    hass_storage[dashboard.DASHBOARDS_STORAGE_KEY] = {
        "version": 1,
        "key": dashboard.DASHBOARDS_STORAGE_KEY,
        "data": {
            "items": [
                {
                    "id": "lovelace",
                    "url_path": "lovelace",
                    "title": "Overview",
                    "icon": "mdi:view-dashboard",
                    "show_in_sidebar": True,
                    "require_admin": False,
                    "mode": "storage",
                }
            ]
        },
    }
    hass_storage[dashboard.CONFIG_STORAGE_KEY.format("lovelace")] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY.format("lovelace"),
        "data": {"config": {"views": [{"title": "Home"}]}},
    }
    # Also have old file (should be ignored since dashboard exists)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Old"}]}},
    }

    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    # Only the pre-existing dashboard, no duplicate
    expect(len(response["result"])).to_equal(1)
    expect(response["result"][0]["url_path"]).to_equal("lovelace")

    # Old storage should still exist (not touched)
    expect(dashboard.CONFIG_STORAGE_KEY_DEFAULT in hass_storage).to_be(True)


@test
async def lovelace_from_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we load lovelace config from yaml."""
    expect(
        await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "YAML"}})
    ).to_be(True)
    expect(hass.data[frontend.DATA_PANELS]["lovelace"].config).to_equal(
        {"mode": "yaml"}
    )

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config"})
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    expect(response["error"]["code"]).to_equal("config_not_found")

    # Store new config not allowed
    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    # Patch data
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo"},
    ):
        await client.send_json({"id": 7, "type": "lovelace/config"})
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo"})

    expect(len(events)).to_equal(0)

    # Fake new data to see we fire event
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo2"},
    ):
        await client.send_json({"id": 8, "type": "lovelace/config", "force": True})
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo2"})

    expect(len(events)).to_equal(1)

    # Make sure when the mtime changes, we reload the config
    with (
        patch(
            "homeassistant.components.lovelace.dashboard.load_yaml_dict",
            return_value={"hello": "yo3"},
        ),
        patch(
            "homeassistant.components.lovelace.dashboard.os.path.getmtime",
            return_value=time.time(),
        ),
    ):
        await client.send_json({"id": 9, "type": "lovelace/config", "force": False})
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo3"})

    expect(len(events)).to_equal(2)

    # If the mtime is lower, preserve the cache
    with (
        patch(
            "homeassistant.components.lovelace.dashboard.load_yaml_dict",
            return_value={"hello": "yo4"},
        ),
        patch(
            "homeassistant.components.lovelace.dashboard.os.path.getmtime",
            return_value=0,
        ),
    ):
        await client.send_json({"id": 10, "type": "lovelace/config", "force": False})
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo3"})

    expect(len(events)).to_equal(2)


@test
async def lovelace_from_yaml_creates_repair_issue(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test YAML mode creates a repair issue."""
    expect(
        await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "YAML"}})
    ).to_be(True)

    # Panel should be registered as a YAML dashboard
    expect(hass.data[frontend.DATA_PANELS]["lovelace"].config).to_equal(
        {"mode": "yaml"}
    )

    # Repair issue should be created
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue("lovelace", "yaml_mode_deprecated")
    expect(issue is not None).to_be(True)
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.is_fixable).to_be(False)
    expect(issue.breaks_in_ha_version).to_equal("2026.8.0")


@test.cases(
    test.case("test-panel", url_path="test-panel"),
    test.case("test-panel-no-sidebar", url_path="test-panel-no-sidebar"),
)
async def dashboard_from_yaml(
    url_path: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we load lovelace dashboard config from yaml."""
    expect(
        await async_setup_component(
            hass,
            "lovelace",
            {
                "lovelace": {
                    "dashboards": {
                        "test-panel": {
                            "mode": "yaml",
                            "filename": "bla.yaml",
                            "title": "Test Panel",
                            "icon": "mdi:test-icon",
                            "show_in_sidebar": False,
                            "require_admin": True,
                        },
                        "test-panel-no-sidebar": {
                            "title": "Title No Sidebar",
                            "mode": "yaml",
                            "filename": "bla2.yaml",
                        },
                    }
                }
            },
        )
    ).to_be(True)
    expect(hass.data[frontend.DATA_PANELS]["test-panel"].config).to_equal(
        {"mode": "yaml"}
    )
    expect(hass.data[frontend.DATA_PANELS]["test-panel-no-sidebar"].config).to_equal(
        {"mode": "yaml"}
    )

    client = await hass_ws_client(hass)

    # List dashboards
    await client.send_json({"id": 4, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(2)
    with_sb, without_sb = response["result"]

    expect(with_sb["mode"]).to_equal("yaml")
    expect(with_sb["filename"]).to_equal("bla.yaml")
    expect(with_sb["title"]).to_equal("Test Panel")
    expect(with_sb["icon"]).to_equal("mdi:test-icon")
    expect(with_sb["show_in_sidebar"]).to_be(False)
    expect(with_sb["require_admin"]).to_be(True)
    expect(with_sb["url_path"]).to_equal("test-panel")

    expect(without_sb["mode"]).to_equal("yaml")
    expect(without_sb["filename"]).to_equal("bla2.yaml")
    expect(without_sb["show_in_sidebar"]).to_be(True)
    expect(without_sb["require_admin"]).to_be(False)
    expect(without_sb["url_path"]).to_equal("test-panel-no-sidebar")

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config", "url_path": url_path})
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    expect(response["error"]["code"]).to_equal("config_not_found")

    # Store new config not allowed
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/config/save",
            "config": {"yo": "hello"},
            "url_path": url_path,
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    # Patch data
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo"},
    ):
        await client.send_json(
            {"id": 7, "type": "lovelace/config", "url_path": url_path}
        )
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo"})

    expect(len(events)).to_equal(0)

    # Fake new data to see we fire event
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"hello": "yo2"},
    ):
        await client.send_json(
            {"id": 8, "type": "lovelace/config", "force": True, "url_path": url_path}
        )
        response = await client.receive_json()

    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"hello": "yo2"})

    expect(len(events)).to_equal(1)


@test
async def wrong_key_dashboard_from_yaml(
    hass: HomeAssistant = Depends(hass_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we don't load lovelace dashboard without hyphen config from yaml."""
    with assert_setup_component(0, "lovelace"):
        expect(
            await async_setup_component(
                hass,
                "lovelace",
                {
                    "lovelace": {
                        "dashboards": {
                            "testpanel": {
                                "mode": "yaml",
                                "filename": "bla.yaml",
                                "title": "Test Panel",
                                "icon": "mdi:test-icon",
                                "show_in_sidebar": False,
                                "require_admin": True,
                            }
                        }
                    }
                },
            )
        ).to_be(False)


@test
async def storage_dashboards(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test we load lovelace config from storage."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Default lovelace panel is registered for backward compatibility
    expect("lovelace" in hass.data[frontend.DATA_PANELS]).to_be(True)

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])

    # Add a wrong dashboard (no hyphen)
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "path",
            "title": "Test path without hyphen",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)

    # Add a dashboard
    await client.send_json(
        {
            "id": 7,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "require_admin": True,
            "title": "New Title",
            "icon": "mdi:map",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]["require_admin"]).to_be(True)
    expect(response["result"]["title"]).to_equal("New Title")
    expect(response["result"]["icon"]).to_equal("mdi:map")

    dashboard_id = response["result"]["id"]

    expect("created-url-path" in hass.data[frontend.DATA_PANELS]).to_be(True)

    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(1)
    expect(response["result"][0]["mode"]).to_equal("storage")
    expect(response["result"][0]["title"]).to_equal("New Title")
    expect(response["result"][0]["icon"]).to_equal("mdi:map")
    expect(response["result"][0]["show_in_sidebar"]).to_be(True)
    expect(response["result"][0]["require_admin"]).to_be(True)

    # Fetch config
    await client.send_json(
        {"id": 9, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)
    expect(response["error"]["code"]).to_equal("config_not_found")

    # Store new config
    events = async_capture_events(hass, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {
            "id": 10,
            "type": "lovelace/config/save",
            "url_path": "created-url-path",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(
        hass_storage[dashboard.CONFIG_STORAGE_KEY.format(dashboard_id)]["data"]
    ).to_equal({"config": {"yo": "hello"}})
    expect(len(events)).to_equal(1)
    expect(events[0].data["url_path"]).to_equal("created-url-path")

    await client.send_json(
        {"id": 11, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"yo": "hello"})

    # Update a dashboard
    await client.send_json(
        {
            "id": 12,
            "type": "lovelace/dashboards/update",
            "dashboard_id": dashboard_id,
            "require_admin": False,
            "icon": "mdi:updated",
            "show_in_sidebar": False,
            "title": "Updated Title",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]["mode"]).to_equal("storage")
    expect(response["result"]["url_path"]).to_equal("created-url-path")
    expect(response["result"]["title"]).to_equal("Updated Title")
    expect(response["result"]["icon"]).to_equal("mdi:updated")
    expect(response["result"]["show_in_sidebar"]).to_be(False)
    expect(response["result"]["require_admin"]).to_be(False)

    # List dashboards again and make sure we see latest config
    await client.send_json({"id": 13, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(1)
    expect(response["result"][0]["mode"]).to_equal("storage")
    expect(response["result"][0]["url_path"]).to_equal("created-url-path")
    expect(response["result"][0]["title"]).to_equal("Updated Title")
    expect(response["result"][0]["icon"]).to_equal("mdi:updated")
    expect(response["result"][0]["show_in_sidebar"]).to_be(False)
    expect(response["result"][0]["require_admin"]).to_be(False)

    # Add a wrong dashboard (missing title)
    await client.send_json(
        {
            "id": 14,
            "type": "lovelace/dashboards/create",
            "url_path": "path",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)
    expect(response["error"]["code"]).to_equal("invalid_format")

    # Add dashboard with existing url path
    await client.send_json(
        {
            "id": 15,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "title": "Another title",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(False)
    expect(response["error"]["code"]).to_equal("home_assistant_error")
    expect(response["error"]["translation_key"]).to_equal("url_already_exists")
    expect(response["error"]["translation_placeholders"]["url"]).to_equal(
        "created-url-path"
    )

    # Delete dashboards
    await client.send_json(
        {"id": 16, "type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    expect("created-url-path" in hass.data[frontend.DATA_PANELS]).to_be(False)
    expect(dashboard.CONFIG_STORAGE_KEY.format(dashboard_id) in hass_storage).to_be(
        False
    )


@test
async def websocket_list_dashboards(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test listing dashboards both storage + YAML."""
    expect(
        await async_setup_component(
            hass,
            "lovelace",
            {
                "lovelace": {
                    "dashboards": {
                        "test-panel-no-sidebar": {
                            "title": "Test YAML",
                            "mode": "yaml",
                            "filename": "bla.yaml",
                        },
                    }
                }
            },
        )
    ).to_be(True)

    client = await hass_ws_client(hass)

    # Create a storage dashboard
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "title": "Test Storage",
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    # List dashboards
    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(response["result"])).to_equal(2)
    with_sb, without_sb = response["result"]

    expect(with_sb["mode"]).to_equal("yaml")
    expect(with_sb["title"]).to_equal("Test YAML")
    expect(with_sb["filename"]).to_equal("bla.yaml")
    expect(with_sb["url_path"]).to_equal("test-panel-no-sidebar")

    expect(without_sb["mode"]).to_equal("storage")
    expect(without_sb["title"]).to_equal("Test Storage")
    expect(without_sb["url_path"]).to_equal("created-url-path")


@test
async def lovelace_migration_sets_default_panel(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test migration sets default_panel to lovelace when not configured."""
    # Pre-populate storage with existing lovelace config
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }

    # Need to setup frontend to register the websocket commands
    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Verify default_panel was set in frontend system storage via websocket
    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "frontend/get_system_data", "key": "core"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]["value"]["default_panel"]).to_equal("lovelace")


@test
async def lovelace_migration_preserves_existing_default_panel(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test migration does not override existing default_panel."""
    # Pre-populate storage with existing lovelace config
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "version": 1,
        "key": dashboard.CONFIG_STORAGE_KEY_DEFAULT,
        "data": {"config": {"views": [{"title": "Home"}]}},
    }
    # Pre-populate frontend system storage with existing default_panel
    storage_key = f"{frontend.DOMAIN}.system_data"
    hass_storage[storage_key] = {
        "version": 1,
        "key": storage_key,
        "data": {"core": {"default_panel": "other-dashboard"}},
    }

    # Need to setup frontend to register the websocket commands
    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Verify default_panel was NOT overwritten via websocket
    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "frontend/get_system_data", "key": "core"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]["value"]["default_panel"]).to_equal("other-dashboard")


@test
async def lovelace_no_migration_no_default_panel_set(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test no default_panel is set when there's nothing to migrate."""
    # Need to setup frontend to register the websocket commands
    expect(await async_setup_component(hass, "frontend", {})).to_be(True)
    # No pre-existing lovelace storage = no migration
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    # Verify default_panel was NOT set via websocket
    client = await hass_ws_client(hass)
    await client.send_json({"id": 5, "type": "frontend/get_system_data", "key": "core"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]["value"] is None).to_be(True)


@test
async def lovelace_info_default(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test lovelace/info returns default resource_mode."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    client = await hass_ws_client(hass)

    await client.send_json({"id": 5, "type": "lovelace/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"resource_mode": "storage"})


@test
async def lovelace_info_yaml_resource_mode(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test lovelace/info returns yaml resource_mode."""
    expect(
        await async_setup_component(
            hass, "lovelace", {"lovelace": {"resource_mode": "yaml"}}
        )
    ).to_be(True)

    client = await hass_ws_client(hass)

    await client.send_json({"id": 5, "type": "lovelace/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"resource_mode": "yaml"})


@test
async def lovelace_info_yaml_mode_fallback(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    _onboarding: MagicMock = Depends(mock_onboarding_done_fx),
) -> None:
    """Test lovelace/info returns yaml resource_mode when mode is yaml."""
    expect(
        await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "yaml"}})
    ).to_be(True)

    client = await hass_ws_client(hass)

    await client.send_json({"id": 5, "type": "lovelace/info"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal({"resource_mode": "yaml"})
