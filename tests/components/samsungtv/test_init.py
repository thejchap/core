"""Tests for the Samsung TV Integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.samsungtv.const import (
    CONF_SESSION_ID,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_MAC, CONF_TOKEN
from homeassistant.core import HomeAssistant

from . import setup_samsungtv_entry
from ._fixtures import (
    app_list_delay,
    fake_host,
    mac_address,
    mock_setup_entry,
    rest_api,
    remote_encrypted_websocket,
    remote_websocket,
    samsungtv_mock_async_get_local_ip,
    silent_ssdp_scanner,
    upnp_factory,
)
from .const import ENTRYDATA_ENCRYPTED_WEBSOCKET, ENTRYDATA_WEBSOCKET

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ssdp: None = Depends(silent_ssdp_scanner),
    _host: None = Depends(fake_host),
    _local_ip: None = Depends(samsungtv_mock_async_get_local_ip),
    _app_list: None = Depends(app_list_delay),
    _mac: None = Depends(mac_address),
    _upnp: None = Depends(upnp_factory),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture (autouse for the module)."""
    return hass


@test
async def reauth_triggered_encrypted(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test reauth flow is triggered for encrypted TVs missing tokens."""
    encrypted_entry_data = {**ENTRYDATA_ENCRYPTED_WEBSOCKET}
    del encrypted_entry_data[CONF_TOKEN]
    del encrypted_entry_data[CONF_SESSION_ID]

    entry = await setup_samsungtv_entry(hass, encrypted_entry_data)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    flows_in_progress = [
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["context"]["source"] == "reauth"
    ]
    expect(len(flows_in_progress)).to_equal(1)


@test
async def incorrectly_formatted_mac_fixed(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ws: None = Depends(remote_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test incorrectly formatted mac is corrected on setup."""
    await setup_samsungtv_entry(
        hass,
        {**ENTRYDATA_WEBSOCKET, CONF_MAC: "aabbaaaaaaaa"},
    )
    await hass.async_block_till_done()

    config_entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(config_entries)).to_equal(1)
    expect(config_entries[0].data[CONF_MAC]).to_equal("aa:bb:aa:aa:aa:aa")


@test.skip("syrupy snapshot")
async def setup() -> None:
    """Stub for test_setup."""

@test.skip("caplog assertion: pending caplog shim")
async def setup_h_j_model() -> None:
    """Stub for test_setup_h_j_model."""

@test.skip("complex SSDP discovery cache patches; pending fixtures")
async def setup_updates_from_ssdp() -> None:
    """Stub for test_setup_updates_from_ssdp."""
