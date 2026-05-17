"""The tests for the Rfxtrx component."""

from unittest.mock import ANY, MagicMock, Mock, call

import RFXtrx as rfxtrxmod
from tryke import Depends, expect, fixture, test

from homeassistant.components.rfxtrx.const import EVENT_RFXTRX_EVENT
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from ._fixtures import connect_mock, rfxtrx_fx, setup_rfx_test_cfg, transport_mock

from tests.hass_fixtures import (
    ClientSessionGenerator,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_access_token as hass_access_token_fixture,
    hass_ws_client as hass_ws_client_fixture,
)

SOME_PROTOCOLS = ["ac", "arc"]


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def fire_event(
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test fire event."""
    await setup_rfx_test_cfg(
        hass,
        device="/dev/serial/by-id/usb-RFXCOM_RFXtrx433_A1Y0NJGR-if00-port0",
        automatic_add=True,
        devices={
            "0b1100cd0213c7f210010f51": {},
            "0716000100900970": {},
        },
    )

    calls = []

    @callback
    def record_event(event):
        """Add recorded event to set."""
        expect(event.event_type).to_equal("rfxtrx_event")
        calls.append(event.data)

    hass.bus.async_listen(EVENT_RFXTRX_EVENT, record_event)

    await rfxtrx.signal("0b1100cd0213c7f210010f51")
    await rfxtrx.signal("0716000100900970")

    device_id_1 = device_registry.async_get_device(
        identifiers={("rfxtrx", "11", "0", "213c7f2:16")}
    )
    expect(device_id_1 is not None).to_be(True)

    device_id_2 = device_registry.async_get_device(
        identifiers={("rfxtrx", "16", "0", "00:90")}
    )
    expect(device_id_2 is not None).to_be(True)

    expect(calls).to_equal(
        [
            {
                "packet_type": 17,
                "sub_type": 0,
                "type_string": "AC",
                "id_string": "213c7f2:16",
                "data": "0b1100cd0213c7f210010f51",
                "values": {"Command": "On", "Rssi numeric": 5},
                "device_id": device_id_1.id,
            },
            {
                "packet_type": 22,
                "sub_type": 0,
                "type_string": "Byron SX",
                "id_string": "00:90",
                "data": "0716000100900970",
                "values": {"Command": "Sound 9", "Rssi numeric": 7, "Sound": 9},
                "device_id": device_id_2.id,
            },
        ]
    )


@test
async def send(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test configuration."""
    await setup_rfx_test_cfg(hass, device="/dev/null", devices={})

    await hass.services.async_call(
        "rfxtrx", "send", {"event": "0a520802060101ff0f0269"}, blocking=True
    )

    expect(rfxtrx.transport.send.mock_calls).to_equal(
        [call(bytearray(b"\x0a\x52\x08\x02\x06\x01\x01\xff\x0f\x02\x69"))]
    )


@test
async def ws_device_remove(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test removing a device through device registry."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)

    device_id = ["11", "0", "213c7f2:16"]
    mock_entry = await setup_rfx_test_cfg(
        hass,
        devices={
            "0b1100cd0213c7f210010f51": {"fire_event": True, "device_id": device_id},
        },
    )

    device_entry = device_registry.async_get_device(
        identifiers={("rfxtrx", *device_id)}
    )
    expect(device_entry is not None).to_be(True)

    # Ask to remove existing device
    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, mock_entry.entry_id)
    expect(response["success"]).to_be(True)

    # Verify device entry is removed
    expect(
        device_registry.async_get_device(identifiers={("rfxtrx", *device_id)}) is None
    ).to_be(True)

    # Verify that the config entry has removed the device
    expect(mock_entry.data["devices"]).to_equal({})


@test
async def connect(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    connect_mock_fx: MagicMock = Depends(connect_mock),
    transport_mock_fx: Mock = Depends(transport_mock),
) -> None:
    """Test that we attempt to connect to the device."""
    config_entry = await setup_rfx_test_cfg(hass, device="/dev/ttyUSBfake")
    transport_mock_fx.assert_called_once_with("/dev/ttyUSBfake")
    connect_mock_fx.assert_called_once_with(
        transport_mock_fx.return_value, ANY, modes=ANY
    )
    rfxtrx.connect.assert_called_once_with(ANY)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def connect_network(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    connect_mock_fx: MagicMock = Depends(connect_mock),
    transport_mock_fx: Mock = Depends(transport_mock),
) -> None:
    """Test that we attempt to connect to the device."""
    config_entry = await setup_rfx_test_cfg(hass, host="localhost", port=1234)
    transport_mock_fx.assert_called_once_with(("localhost", 1234))
    connect_mock_fx.assert_called_once_with(
        transport_mock_fx.return_value, ANY, modes=ANY
    )
    rfxtrx.connect.assert_called_once_with(ANY)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def connect_with_protocols(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    connect_mock_fx: MagicMock = Depends(connect_mock),
    transport_mock_fx: Mock = Depends(transport_mock),
) -> None:
    """Test that we attempt to set protocols."""
    config_entry = await setup_rfx_test_cfg(
        hass, device="/dev/ttyUSBfake", protocols=SOME_PROTOCOLS
    )
    transport_mock_fx.assert_called_once_with("/dev/ttyUSBfake")
    connect_mock_fx.assert_called_once_with(
        transport_mock_fx.return_value, ANY, modes=SOME_PROTOCOLS
    )
    rfxtrx.connect.assert_called_once_with(ANY)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def connect_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    connect_mock_fx: MagicMock = Depends(connect_mock),
    transport_mock_fx: Mock = Depends(transport_mock),
) -> None:
    """Test that we attempt to connect to the device."""
    rfxtrx.connect.side_effect = TimeoutError

    config_entry = await setup_rfx_test_cfg(hass, device="/dev/ttyUSBfake")
    transport_mock_fx.assert_called_once_with("/dev/ttyUSBfake")
    connect_mock_fx.assert_called_once_with(
        transport_mock_fx.return_value, ANY, modes=ANY
    )
    rfxtrx.connect.assert_called_once_with(ANY)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def connect_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    connect_mock_fx: MagicMock = Depends(connect_mock),
    transport_mock_fx: Mock = Depends(transport_mock),
) -> None:
    """Test that we attempt to connect to the device."""
    rfxtrx.connect.side_effect = rfxtrxmod.RFXtrxTransportError

    config_entry = await setup_rfx_test_cfg(hass, device="/dev/ttyUSBfake")
    transport_mock_fx.assert_called_once_with("/dev/ttyUSBfake")
    connect_mock_fx.assert_called_once_with(
        transport_mock_fx.return_value, ANY, modes=ANY
    )
    rfxtrx.connect.assert_called_once_with(ANY)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def reconnect(
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test that we reconnect on connection loss."""
    config_entry = await setup_rfx_test_cfg(hass, device="/dev/ttyUSBfake")

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    rfxtrx.connect.call_count = 1

    await hass.async_add_executor_job(
        rfxtrx.event_callback,
        rfxtrxmod.ConnectionLost(),
    )
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    rfxtrx.connect.call_count = 2
