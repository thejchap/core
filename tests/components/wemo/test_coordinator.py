"""Tests for wemo_device.py."""

import asyncio
from collections.abc import Generator
from dataclasses import asdict
from datetime import timedelta
from unittest.mock import MagicMock, _Call, call, patch

import pywemo
from pywemo.exceptions import ActionException, PyWeMoException
from pywemo.subscribe import EVENT_TYPE_LONG_PRESS
from tryke import Depends, expect, fixture, test

from homeassistant.components.wemo import CONF_DISCOVERY, CONF_STATIC
from homeassistant.components.wemo.const import DOMAIN, WEMO_SUBSCRIPTION_EVENT
from homeassistant.components.wemo.coordinator import Options, async_get_coordinator
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from ._fixtures import (
    MOCK_FIRMWARE_VERSION,
    MOCK_HOST,
    MOCK_SERIAL_NUMBER,
    async_create_wemo_entity,
    create_pywemo_device,
    pywemo_discovery_responder,
    pywemo_registry,
    wemo_entity_suffix,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    hass as hass_fixture,
    mock_network,
)


# Module-level pywemo_model overrides the default from _fixtures.py.
@fixture
def pywemo_model() -> str:
    """Pywemo LightSwitch models use the switch platform."""
    return "LightSwitchLongPress"


@fixture
def pywemo_device(
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_model: str = Depends(pywemo_model),
) -> Generator[pywemo.WeMoDevice]:
    """Fixture for WeMoDevice instances."""
    with create_pywemo_device(pywemo_registry, pywemo_model) as device:
        yield device


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _responder: None = Depends(pywemo_discovery_responder),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def async_register_device_longpress_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Device is still registered if ensure_long_press_virtual_device fails."""
    with patch.object(pywemo_device, "ensure_long_press_virtual_device") as elp:
        elp.side_effect = PyWeMoException
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {
                    DOMAIN: {
                        CONF_DISCOVERY: False,
                        CONF_STATIC: [MOCK_HOST],
                    },
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()
    device_entries = list(device_registry.devices.values())
    expect(len(device_entries)).to_equal(1)
    device = async_get_coordinator(hass, device_entries[0].id)
    expect(device.supports_long_press).to_be(False)


@test
async def long_press_event(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Device fires a long press event."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device = async_get_coordinator(hass, wemo_entity.device_id)
    got_event = asyncio.Event()
    event_data: dict = {}

    @callback
    def async_event_received(event):
        nonlocal event_data
        event_data = event.data
        got_event.set()

    hass.bus.async_listen_once(WEMO_SUBSCRIPTION_EVENT, async_event_received)

    await hass.async_add_executor_job(
        pywemo_registry.callbacks[device.wemo.name],
        device.wemo,
        EVENT_TYPE_LONG_PRESS,
        "testing_params",
    )

    async with asyncio.timeout(8):
        await got_event.wait()

    expect(event_data).to_equal(
        {
            "device_id": wemo_entity.device_id,
            "name": device.wemo.name,
            "params": "testing_params",
            "type": EVENT_TYPE_LONG_PRESS,
            "unique_id": device.wemo.serial_number,
        }
    )


@test
async def subscription_callback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Device processes a registry subscription callback."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device = async_get_coordinator(hass, wemo_entity.device_id)
    device.last_update_success = False

    got_callback = asyncio.Event()

    @callback
    def async_received_callback():
        got_callback.set()

    device.async_add_listener(async_received_callback)

    await hass.async_add_executor_job(
        pywemo_registry.callbacks[device.wemo.name], device.wemo, "", ""
    )

    async with asyncio.timeout(8):
        await got_callback.wait()
    expect(device.last_update_success).to_be(True)


@test
async def subscription_update_action_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Device handles ActionException on get_state properly."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device = async_get_coordinator(hass, wemo_entity.device_id)
    device.last_update_success = True

    pywemo_device.subscription_update.return_value = False
    pywemo_device.get_state.reset_mock()
    pywemo_device.get_state.side_effect = ActionException
    await hass.async_add_executor_job(
        device.subscription_callback, pywemo_device, "", ""
    )
    await hass.async_block_till_done()

    pywemo_device.get_state.assert_called_once_with(True)
    expect(device.last_update_success).to_be(False)
    expect(isinstance(device.last_exception, UpdateFailed)).to_be(True)


@test
async def subscription_update_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Device handles Exception on get_state properly."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device = async_get_coordinator(hass, wemo_entity.device_id)
    device.last_update_success = True

    pywemo_device.subscription_update.return_value = False
    pywemo_device.get_state.reset_mock()
    pywemo_device.get_state.side_effect = Exception
    await hass.async_add_executor_job(
        device.subscription_callback, pywemo_device, "", ""
    )
    await hass.async_block_till_done()

    pywemo_device.get_state.assert_called_once_with(True)
    expect(device.last_update_success).to_be(False)
    expect(isinstance(device.last_exception, Exception)).to_be(True)


@test
async def async_update_data_subscribed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """No update happens when the device is subscribed."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device = async_get_coordinator(hass, wemo_entity.device_id)
    pywemo_registry.is_subscribed.return_value = True
    pywemo_device.get_state.reset_mock()
    await device._async_update_data()
    pywemo_device.get_state.assert_not_called()


@test
async def device_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Verify the DeviceInfo data is set properly."""
    await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    device_entries = list(device_registry.devices.values())

    expect(len(device_entries)).to_equal(1)
    expect(device_entries[0].connections).to_equal(
        {("upnp", f"uuid:LightSwitch-1_0-{MOCK_SERIAL_NUMBER}")}
    )
    expect(device_entries[0].manufacturer).to_equal("Belkin")
    expect(device_entries[0].model).to_equal("LightSwitch")
    expect(device_entries[0].model_id).to_equal("LightSwitch")
    expect(device_entries[0].sw_version).to_equal(MOCK_FIRMWARE_VERSION)


@test
async def dli_device_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_model: str = Depends(pywemo_model),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Verify the DeviceInfo data for Digital Loggers emulated wemo device."""
    with create_pywemo_device(pywemo_registry, pywemo_model) as device:
        device.model_name = "DLI emulated Belkin Socket"
        device.serial_number = "1234567891"
        await async_create_wemo_entity(hass, device, wemo_entity_suffix)

    device_entries = list(device_registry.devices.values())

    expect(device_entries[0].configuration_url).to_equal("http://127.0.0.1")
    expect(device_entries[0].identifiers).to_equal({(DOMAIN, "123456789")})


@test
async def options_enable_subscription_false(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Test setting Options.enable_subscription = False."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    config_entry = hass.config_entries.async_get_entry(wemo_entity.config_entry_id)
    expect(
        hass.config_entries.async_update_entry(
            config_entry,
            options=asdict(
                Options(enable_subscription=False, enable_long_press=False)
            ),
        )
    ).to_be(True)
    await hass.async_block_till_done()
    pywemo_registry.unregister.assert_called_once_with(pywemo_device)


@test
async def options_enable_long_press_false(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Test setting Options.enable_long_press = False."""
    wemo_entity = await async_create_wemo_entity(hass, pywemo_device, wemo_entity_suffix)
    config_entry = hass.config_entries.async_get_entry(wemo_entity.config_entry_id)
    expect(
        hass.config_entries.async_update_entry(
            config_entry, options=asdict(Options(enable_long_press=False))
        )
    ).to_be(True)
    await hass.async_block_till_done()
    pywemo_device.remove_long_press_virtual_device.assert_called_once_with()


# --- Insight tests (originally TestInsight class) -------------------------
#
# Module-level fixtures in tryke run for EVERY test in the file. To avoid
# Insight's device-patches colliding with the LightSwitch ones used by the
# rest of the module, set up the Insight device inline within the test.


@test.cases(
    test.case(
        "not_subscribed_off",
        subscribed=False,
        state=0,
        expected_calls=[call(), call(True), call(), call()],
    ),
    test.case(
        "not_subscribed_on",
        subscribed=False,
        state=1,
        expected_calls=[call(), call(True), call(), call()],
    ),
    test.case(
        "subscribed_off",
        subscribed=True,
        state=0,
        expected_calls=[call(), call(True), call(), call()],
    ),
    test.case(
        "subscribed_on",
        subscribed=True,
        state=1,
        expected_calls=[call(), call(), call()],
    ),
)
async def insight_should_poll(
    subscribed: bool,
    state: int,
    expected_calls: list[_Call],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
    wemo_entity_suffix: str = Depends(wemo_entity_suffix),
) -> None:
    """Validate the should_poll returns the correct value."""
    with create_pywemo_device(pywemo_registry, "Insight") as insight_device:
        insight_device.insight_params = {
            "currentpower": 1.0,
            "todaymw": 200000000.0,
            "state": 0,
            "onfor": 0,
            "ontoday": 0,
            "ontotal": 0,
            "powerthreshold": 0,
        }
        await async_create_wemo_entity(hass, insight_device, wemo_entity_suffix)

        pywemo_registry.is_subscribed.return_value = subscribed
        insight_device.get_state.reset_mock()
        insight_device.get_state.return_value = state
        async_fire_time_changed(hass, utcnow() + timedelta(seconds=31))
        await hass.async_block_till_done()
        insight_device.get_state.assert_has_calls(expected_calls)
