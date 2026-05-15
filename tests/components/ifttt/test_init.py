"""Test the init file of IFTTT."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import ifttt
from homeassistant.core import HomeAssistant, callback
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def config_flow_registers_webhook(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test setting up IFTTT and sending webhook."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )

    result = await hass.config_entries.flow.async_init(
        "ifttt", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    webhook_id = result["result"].data["webhook_id"]

    ifttt_events = []

    @callback
    def handle_event(event):
        """Handle IFTTT event."""
        ifttt_events.append(event)

    hass.bus.async_listen(ifttt.EVENT_RECEIVED, handle_event)

    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{webhook_id}", json={"hello": "ifttt"})

    expect(len(ifttt_events)).to_equal(1)
    expect(ifttt_events[0].data["webhook_id"]).to_equal(webhook_id)
    expect(ifttt_events[0].data["hello"]).to_equal("ifttt")

    await client.post(f"/api/webhook/{webhook_id}", data="not a dict")
    expect(len(ifttt_events)).to_equal(1)

    await client.post(f"/api/webhook/{webhook_id}", json="not a dict")
    expect(len(ifttt_events)).to_equal(1)
