"""Test the Z-Wave JS init module (tryke port).

Ports the simpler tests from dev's ``test_init.py``. Tests that need
supervisor add-on shims, complex async listen replay, or device-registry
fixtures beyond the deep-mock chain remain skipped with specific reasons.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    client,
    connect_timeout,
    integration,
    integration_no_platforms,
    listen_block,
    multisensor_6,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture — see PATTERNS.md `_trigger_executor` note."""


# ---------------------------------------------------------------------------
# Smoke tests — `client` + `integration` deep mock chain.
# ---------------------------------------------------------------------------


@test("integration setup and unload calls connect/disconnect once")
async def entry_setup_unload(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test the integration set up and unload."""
    entry = integration

    expect(client.connect.call_count).to_be(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entry.entry_id)

    expect(client.disconnect.call_count).to_be(1)
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test("home assistant stop disconnects client")
async def home_assistant_stop(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Test we clean up on home assistant stop."""
    await hass.async_stop()
    expect(client.disconnect.call_count).to_be(1)


@test("connect timeout drives setup retry")
async def initialized_timeout(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
    _timeout: MagicMock = Depends(connect_timeout),
) -> None:
    """Test we handle a timeout during client initialization."""
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test("statistics enabled when opted in")
async def enabled_statistics(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
) -> None:
    """Test that we enabled statistics if the entry is opted in."""
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org", "data_collection_opted_in": True},
    )
    entry.add_to_hass(hass)

    with patch(
        "zwave_js_server.model.driver.Driver.async_enable_statistics"
    ) as mock_cmd:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_cmd.called).to_be(True)


@test("statistics disabled when opted out")
async def disabled_statistics(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
) -> None:
    """Test that we disabled statistics if the entry is opted out."""
    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org", "data_collection_opted_in": False},
    )
    entry.add_to_hass(hass)

    with patch(
        "zwave_js_server.model.driver.Driver.async_disable_statistics"
    ) as mock_cmd:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_cmd.called).to_be(True)


@test("no statistics calls when preference unset")
async def noop_statistics(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(client),
) -> None:
    """Test that we don't make statistics calls if user hasn't set preference."""
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)

    with (
        patch(
            "zwave_js_server.model.driver.Driver.async_enable_statistics"
        ) as mock_cmd1,
        patch(
            "zwave_js_server.model.driver.Driver.async_disable_statistics"
        ) as mock_cmd2,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_cmd1.called).to_be(False)
        expect(mock_cmd2.called).to_be(False)


@test("driver-ready timeout puts entry in setup retry")
async def driver_ready_timeout_during_setup(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
    listen_block: asyncio.Event = Depends(listen_block),
) -> None:
    """Test we handle driver ready timeout during setup."""

    async def listen(driver_ready: asyncio.Event) -> None:
        """Mock listen that never sets driver_ready."""
        await listen_block.wait()

    client.listen.side_effect = listen

    entry = MockConfigEntry(
        domain="zwave_js",
        data={"url": "ws://test.org", "data_collection_opted_in": True},
    )
    entry.add_to_hass(hass)
    expect(client.disconnect.call_count).to_be(0)

    with patch("homeassistant.components.zwave_js.DRIVER_READY_TIMEOUT", new=0):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(client.disconnect.call_count).to_be(1)


@test("integration boots with no platforms (controller-only)")
async def integration_no_platforms_boots(
    _t: None = Depends(_trigger_executor),
    _client: MagicMock = Depends(client),
    integration_no_platforms: MockConfigEntry = Depends(integration_no_platforms),
) -> None:
    """Smoke check that the no-platforms variant of the integration boots."""
    expect(integration_no_platforms.state).to_be(ConfigEntryState.LOADED)


@test("multisensor 6 attaches to controller after integration setup")
async def multisensor_6_attached(
    _t: None = Depends(_trigger_executor),
    client: MagicMock = Depends(client),
    multisensor_6: object = Depends(multisensor_6),
    _integration: MockConfigEntry = Depends(integration),
) -> None:
    """Smoke check that a per-device fixture flows through the chain."""
    nodes = client.driver.controller.nodes
    expect(multisensor_6.node_id in nodes).to_be(True)


# ---------------------------------------------------------------------------
# Skipped tests — require fixtures beyond the deep-mock chain.
# ---------------------------------------------------------------------------


@test.skip(
    "needs hassio addon fixtures (addon_running/addon_installed/install_addon/"
    "start_addon/set_addon_options) — port deferred"
)
async def listen_done_during_setup_before_forward_entry() -> None:
    """Stub for test_listen_done_during_setup_before_forward_entry.

    Requires hassio AddOn fixture chain + indirect parametrize.
    """


@test.skip(
    "needs supervisor addon fixtures + indirect parametrize — port deferred"
)
async def not_connected_during_setup_after_forward_entry() -> None:
    """Stub for test_not_connected_during_setup_after_forward_entry."""


@test.skip(
    "needs supervisor addon fixtures + indirect parametrize — port deferred"
)
async def listen_done_during_setup_after_forward_entry() -> None:
    """Stub for test_listen_done_during_setup_after_forward_entry."""


@test.skip("indirect listen-replay machinery — port deferred")
async def listen_done_after_setup() -> None:
    """Stub for test_listen_done_after_setup."""


@test.skip("indirect listen-replay machinery — port deferred")
async def listen_ending_before_cancelling_listen() -> None:
    """Stub for test_listen_ending_before_cancelling_listen."""


@test.skip("indirect listen-replay machinery — port deferred")
async def listen_ending_unrecoverable_config_entry_state() -> None:
    """Stub for test_listen_ending_unrecoverable_config_entry_state."""


@test.skip("entity-registry value-add path — port deferred")
async def new_entity_on_value_added() -> None:
    """Stub for test_new_entity_on_value_added."""


@test.skip("device-registry/node-added path — port deferred")
async def on_node_added_ready() -> None:
    """Stub for test_on_node_added_ready."""


@test.skip("device-registry pre-provisioning — port deferred")
async def check_pre_provisioned_device_update_device() -> None:
    """Stub for test_check_pre_provisioned_device_update_device."""


@test.skip("device-registry pre-provisioning — port deferred")
async def check_pre_provisioned_device_remove_device() -> None:
    """Stub for test_check_pre_provisioned_device_remove_device."""


@test.skip("device-registry/node-added path — port deferred")
async def on_node_added_not_ready() -> None:
    """Stub for test_on_node_added_not_ready."""


@test.skip("device-registry/node-added path — port deferred")
async def existing_node_ready() -> None:
    """Stub for test_existing_node_ready."""


@test.skip("device-registry/reinterview path — port deferred")
async def existing_node_reinterview() -> None:
    """Stub for test_existing_node_reinterview."""


@test.skip("device-registry/node-added path — port deferred")
async def existing_node_not_ready() -> None:
    """Stub for test_existing_node_not_ready."""


@test.skip("device-registry/node-replace path — port deferred")
async def existing_node_not_replaced_when_not_ready() -> None:
    """Stub for test_existing_node_not_replaced_when_not_ready."""


@test.skip("uses null_name_check fixture — port deferred (needs persistent_notification)")
async def null_name() -> None:
    """Stub for test_null_name."""


@test.skip("hassio addon fixtures — port deferred")
async def start_addon() -> None:
    """Stub for test_start_addon."""


@test.skip("hassio addon fixtures — port deferred")
async def start_addon_redacts_set_options_error() -> None:
    """Stub for test_start_addon_redacts_set_options_error."""


@test.skip("hassio addon fixtures — port deferred")
async def install_addon() -> None:
    """Stub for test_install_addon."""


@test.skip("hassio addon fixtures — port deferred")
async def addon_info_failure() -> None:
    """Stub for test_addon_info_failure."""


@test.skip("hassio addon fixtures — port deferred")
async def addon_options_changed() -> None:
    """Stub for test_addon_options_changed."""


@test.skip("hassio addon fixtures — port deferred")
async def update_addon() -> None:
    """Stub for test_update_addon."""


@test.skip("issue-registry coverage — port deferred")
async def issue_registry() -> None:
    """Stub for test_issue_registry."""


@test.skip("hassio addon fixtures — port deferred")
async def stop_addon() -> None:
    """Stub for test_stop_addon."""


@test.skip("backup/restore + remove_entry path — port deferred")
async def remove_entry() -> None:
    """Stub for test_remove_entry."""


@test.skip("device-registry removal path — port deferred")
async def removed_device() -> None:
    """Stub for test_removed_device."""


@test.skip("device-registry suggested-area — port deferred")
async def suggested_area() -> None:
    """Stub for test_suggested_area."""


@test.skip("device-registry node-removed path — port deferred")
async def node_removed() -> None:
    """Stub for test_node_removed."""


@test.skip("device-registry node-replace path — port deferred")
async def replace_same_node() -> None:
    """Stub for test_replace_same_node."""


@test.skip("device-registry node-replace path — port deferred")
async def replace_different_node() -> None:
    """Stub for test_replace_different_node."""


@test.skip("device-registry node-model-change — port deferred")
async def node_model_change() -> None:
    """Stub for test_node_model_change."""


@test.skip("entity-registry disable path — port deferred")
async def disabled_node_status_entity_on_node_replaced() -> None:
    """Stub for test_disabled_node_status_entity_on_node_replaced."""


@test.skip("entity-registry remove path — port deferred")
async def remove_entity_on_value_removed() -> None:
    """Stub for test_remove_entity_on_value_removed."""


@test.skip("entity-registry value-removed path — port deferred")
async def value_removed_and_readded() -> None:
    """Stub for test_value_removed_and_readded."""


@test.skip("entity-registry value-added path — port deferred")
async def value_never_populated_then_added() -> None:
    """Stub for test_value_never_populated_then_added."""


@test.skip("identify event needs persistent_notification mock — port deferred")
async def identify_event() -> None:
    """Stub for test_identify_event."""


@test.skip("server-logging coverage — port deferred (needs caplog/log_level shim)")
async def server_logging() -> None:
    """Stub for test_server_logging."""


@test.skip("factory-reset node — port deferred")
async def factory_reset_node() -> None:
    """Stub for test_factory_reset_node."""


@test.skip("entity-availability dead-node — port deferred")
async def entity_available_when_node_dead() -> None:
    """Stub for test_entity_available_when_node_dead."""


@test.skip("driver-ready event coverage — port deferred")
async def driver_ready_event() -> None:
    """Stub for test_driver_ready_event."""
