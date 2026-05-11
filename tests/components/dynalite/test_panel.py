"""Test websocket commands for the panel."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components import dynalite, frontend
from homeassistant.components.cover import DEVICE_CLASSES
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def get_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Get the config via websocket."""
    host = "1.2.3.4"
    port = 765

    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: host, CONF_PORT: port},
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 24,
            "type": "dynalite/get-config",
        }
    )

    msg = await client.receive_json()
    expect(bool(msg["success"])).to_be(True)
    result = msg["result"]
    entry_id = entry.entry_id
    expect(result).to_equal(
        {
            "config": {entry_id: {CONF_HOST: host, CONF_PORT: port}},
            "default": {
                "DEFAULT_NAME": dynalite.const.DEFAULT_NAME,
                "DEFAULT_PORT": dynalite.const.DEFAULT_PORT,
                "DEVICE_CLASSES": DEVICE_CLASSES,
            },
        }
    )


@test
async def save_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Save the config via websocket."""
    host1 = "1.2.3.4"
    port1 = 765
    host2 = "5.6.7.8"
    port2 = 432
    host3 = "5.3.2.1"
    port3 = 543

    entry1 = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: host1, CONF_PORT: port1},
    )
    entry1.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry1.entry_id)).to_be(True)
        await hass.async_block_till_done()
    entry2 = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: host2, CONF_PORT: port2},
    )
    entry2.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry2.entry_id)).to_be(True)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 24,
            "type": "dynalite/save-config",
            "entry_id": entry2.entry_id,
            "config": {CONF_HOST: host3, CONF_PORT: port3},
        }
    )

    msg = await client.receive_json()
    expect(bool(msg["success"])).to_be(True)
    expect(msg["result"]).to_equal({})

    existing_entry = hass.config_entries.async_get_entry(entry1.entry_id)
    expect(existing_entry.data).to_equal({CONF_HOST: host1, CONF_PORT: port1})
    modified_entry = hass.config_entries.async_get_entry(entry2.entry_id)
    expect(modified_entry.data[CONF_HOST]).to_equal(host3)
    expect(modified_entry.data[CONF_PORT]).to_equal(port3)


@test
async def save_config_invalid_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Try to update nonexistent entry."""
    host1 = "1.2.3.4"
    port1 = 765
    host2 = "5.6.7.8"
    port2 = 432

    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: host1, CONF_PORT: port1},
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 24,
            "type": "dynalite/save-config",
            "entry_id": "junk",
            "config": {CONF_HOST: host2, CONF_PORT: port2},
        }
    )

    msg = await client.receive_json()
    expect(bool(msg["success"])).to_be(True)
    expect(msg["result"]).to_equal({"error": True})

    existing_entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(existing_entry.data).to_equal({CONF_HOST: host1, CONF_PORT: port1})


@test
async def panel_registration(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the dynalite panel is registered with correct module URL format."""
    with (
        patch(
            "homeassistant.components.dynalite.panel.locate_dir",
            return_value="/mock/path",
        ),
        patch(
            "homeassistant.components.dynalite.panel.get_build_id", return_value="1.2.3"
        ),
    ):
        result = await setup.async_setup_component(hass, dynalite.DOMAIN, {})
        expect(bool(result)).to_be(True)
        await hass.async_block_till_done()

    panels = hass.data.get(frontend.DATA_PANELS, {})
    expect(dynalite.DOMAIN in panels).to_be(True)

    panel = panels[dynalite.DOMAIN]

    expect(panel.frontend_url_path).to_equal(dynalite.DOMAIN)
    expect(panel.config_panel_domain).to_equal(dynalite.DOMAIN)
    expect(panel.require_admin).to_be(True)

    module_url = panel.config["_panel_custom"]["module_url"]
    expect(module_url).to_equal("/dynalite_static/entrypoint-1.2.3.js")
    expect("entrypoint.1.2.3.js" not in module_url).to_be(True)
