"""The tests for Samsung TV device triggers."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.samsungtv.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_samsungtv_entry
from ._fixtures import (
    app_list_delay,
    fake_host,
    mac_address,
    mock_setup_entry,
    rest_api,
    remote_encrypted_websocket,
    samsungtv_mock_async_get_local_ip,
    silent_ssdp_scanner,
    upnp_factory,
)
from .const import ENTRYDATA_ENCRYPTED_WEBSOCKET

from tests.common import async_get_device_automations
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


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
async def get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket),
    _rest: None = Depends(rest_api),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test we get the expected triggers."""
    await setup_samsungtv_entry(hass, ENTRYDATA_ENCRYPTED_WEBSOCKET)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "be9554b9-c9fb-41f4-8920-22da015376a4")}
    )
    expect(device).not_.to_be(None)

    turn_on_trigger = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "samsungtv.turn_on",
        "device_id": device.id,
        "metadata": {},
    }

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )
    expect(turn_on_trigger in triggers).to_be(True)


@test.skip("automation service_calls fixture pending")
async def if_fires_on_turn_on_request() -> None:
    """Stub for test_if_fires_on_turn_on_request."""


@test.skip("automation service_calls fixture pending")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios."""
