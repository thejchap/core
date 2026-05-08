"""The tests for the SamsungTV remote platform."""

from unittest.mock import Mock, patch

from samsungtvws.encrypted.remote import SamsungTVEncryptedCommand
from tryke import Depends, expect, fixture, test

from homeassistant.components.remote import (
    ATTR_COMMAND,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from homeassistant.components.samsungtv.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import setup_samsungtv_entry
from ._fixtures import (
    app_list_delay,
    fake_host,
    mac_address,
    mock_setup_entry,
    rest_api,
    remote_encrypted_websocket,
    remote_legacy,
    remote_websocket,
    samsungtv_mock_async_get_local_ip,
    silent_ssdp_scanner,
    upnp_factory,
)
from .const import ENTRYDATA_ENCRYPTED_WEBSOCKET, ENTRYDATA_LEGACY, ENTRYDATA_WEBSOCKET

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

ENTITY_ID = f"{REMOTE_DOMAIN}.mock_title"


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
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test setup with basic config."""
    await setup_samsungtv_entry(hass, ENTRYDATA_ENCRYPTED_WEBSOCKET)
    expect(bool(hass.states.get(ENTITY_ID))).to_be(True)


@test
async def unique_id(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket),
    _rest: None = Depends(rest_api),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id is set."""
    await setup_samsungtv_entry(hass, ENTRYDATA_ENCRYPTED_WEBSOCKET)
    main = entity_registry.async_get(ENTITY_ID)
    expect(main).not_.to_be(None)
    expect(main.unique_id).to_equal("be9554b9-c9fb-41f4-8920-22da015376a4")


@test
async def send_command_service(
    hass: HomeAssistant = Depends(_trigger_executor),
    enc: Mock = Depends(remote_encrypted_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test the send command service."""
    await setup_samsungtv_entry(hass, ENTRYDATA_ENCRYPTED_WEBSOCKET)

    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_COMMAND: ["dash"]},
        blocking=True,
    )
    expect(enc.send_commands.call_count).to_equal(1)
    commands = enc.send_commands.call_args_list[0].args[0]
    expect(len(commands)).to_equal(1)
    cmd = commands[0]
    expect(isinstance(cmd, SamsungTVEncryptedCommand)).to_be(True)
    expect(cmd.body["param3"]).to_equal("dash")


@test
async def turn_on_wol(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ws: None = Depends(remote_websocket),
    _rest: None = Depends(rest_api),
) -> None:
    """Test turn_on uses Wake-on-LAN."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=ENTRYDATA_WEBSOCKET,
        unique_id="be9554b9-c9fb-41f4-8920-22da015376a4",
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.samsungtv.entity.send_magic_packet"
    ) as mock_send_magic_packet:
        await hass.services.async_call(
            REMOTE_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, True
        )
        await hass.async_block_till_done()
    expect(mock_send_magic_packet.called).to_be(True)


@test
async def turn_on_without_turnon(
    hass: HomeAssistant = Depends(_trigger_executor),
    legacy: Mock = Depends(remote_legacy),
) -> None:
    """Test turn_on raises HomeAssistantError when WoL is not configured."""
    await setup_samsungtv_entry(hass, ENTRYDATA_LEGACY)
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            REMOTE_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, True
        )
    expect(legacy.control.call_count).to_equal(0)


@test.skip("caplog assertion: pending caplog shim")
async def main_services() -> None:
    """Stub for test_main_services."""
