"""Tests for the wemo component."""

import asyncio
from collections.abc import Generator
from datetime import timedelta
from unittest.mock import MagicMock, create_autospec, patch

import pywemo
from tryke import Depends, expect, fixture, test

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.wemo import (
    CONF_DISCOVERY,
    CONF_STATIC,
    WemoDiscovery,
    async_wemo_dispatcher_connect,
)
from homeassistant.components.wemo.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import entity_test_helpers
from ._fixtures import (
    MOCK_FIRMWARE_VERSION,
    MOCK_HOST,
    MOCK_NAME,
    MOCK_PORT,
    MOCK_SERIAL_NUMBER,
    create_pywemo_device,
    pywemo_discovery_responder,
    pywemo_model,
    pywemo_registry,
)

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


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
async def config_no_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Component setup succeeds when there are no config entry for the domain."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)


@test
async def config_no_static(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Component setup succeeds when there are no static config entries."""
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_DISCOVERY: False}})
    ).to_be(True)


@test
async def static_duplicate_static_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
) -> None:
    """Duplicate static entries are merged into a single entity."""
    static_config_entry = f"{MOCK_HOST}:{MOCK_PORT}"
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    CONF_DISCOVERY: False,
                    CONF_STATIC: [
                        static_config_entry,
                        static_config_entry,
                    ],
                },
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    entity_entries = list(entity_registry.entities.values())
    expect(len(entity_entries)).to_equal(1)


@test
async def static_config_with_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
) -> None:
    """Static device with host and port is added and removed."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    CONF_DISCOVERY: False,
                    CONF_STATIC: [f"{MOCK_HOST}:{MOCK_PORT}"],
                },
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    entity_entries = list(entity_registry.entities.values())
    expect(len(entity_entries)).to_equal(1)


@test
async def static_config_without_port(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
) -> None:
    """Static device with host and no port is added and removed."""
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
    entity_entries = list(entity_registry.entities.values())
    expect(len(entity_entries)).to_equal(1)


@test
async def reload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
) -> None:
    """Config entry can be reloaded without errors."""
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

    async def _async_test_entry_and_entity() -> tuple[str, str]:
        await hass.async_block_till_done()

        pywemo_device.get_state.assert_called()
        pywemo_device.get_state.reset_mock()

        pywemo_registry.register.assert_called_once_with(pywemo_device)
        pywemo_registry.register.reset_mock()

        entity_entries = list(entity_registry.entities.values())
        expect(len(entity_entries)).to_equal(1)
        await entity_test_helpers.test_turn_off_state(
            hass, entity_entries[0], SWITCH_DOMAIN
        )

        entries = hass.config_entries.async_entries(DOMAIN)
        expect(len(entries)).to_equal(1)

        return entries[0].entry_id, entity_entries[0].entity_id

    entry_id, entity_id = await _async_test_entry_and_entity()
    pywemo_registry.unregister.assert_not_called()

    expect(await hass.config_entries.async_reload(entry_id)).to_be(True)

    ids = await _async_test_entry_and_entity()
    pywemo_registry.unregister.assert_called_once_with(pywemo_device)
    expect(ids).to_equal((entry_id, entity_id))


@test
async def static_config_with_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Component setup fails if a static host is invalid."""
    setup_success = await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [""],
            },
        },
    )
    expect(setup_success).to_be(False)


@test
async def static_with_upnp_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_device: pywemo.WeMoDevice = Depends(pywemo_device),
) -> None:
    """Device that fails to get state is not added."""
    pywemo_device.get_state.side_effect = pywemo.exceptions.ActionException("Failed")
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    CONF_DISCOVERY: False,
                    CONF_STATIC: [f"{MOCK_HOST}:{MOCK_PORT}"],
                },
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    entity_entries = list(entity_registry.entities.values())
    expect(len(entity_entries)).to_equal(0)
    pywemo_device.get_state.assert_called_once()


@test
async def discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    pywemo_registry: MagicMock = Depends(pywemo_registry),
) -> None:
    """Verify that discovery dispatches devices to the platform for setup."""

    def create_device(counter):
        """Create a unique mock Motion detector device for each counter value."""
        device = create_autospec(pywemo.Motion, instance=True)
        device.host = f"{MOCK_HOST}_{counter}"
        device.port = MOCK_PORT + counter
        device.name = f"{MOCK_NAME}_{counter}"
        device.serial_number = f"{MOCK_SERIAL_NUMBER}_{counter}"
        device.model_name = "Motion"
        device.model = "Motion"
        device.udn = f"uuid:{device.model_name}-1_0-{device.serial_number}"
        device.firmware_version = MOCK_FIRMWARE_VERSION
        device.get_state.return_value = 0  # Default to Off
        device.supports_long_press.return_value = False
        return device

    semaphore = asyncio.Semaphore(value=0)

    async def async_connect(*args):
        await async_wemo_dispatcher_connect(*args)
        semaphore.release()

    pywemo_devices = [create_device(0), create_device(1)]
    with (
        patch("pywemo.discover_devices", return_value=pywemo_devices) as mock_discovery,
        patch(
            "homeassistant.components.wemo.WemoDiscovery.discover_statics"
        ) as mock_discover_statics,
        patch(
            "homeassistant.components.wemo.binary_sensor.async_wemo_dispatcher_connect",
            side_effect=async_connect,
        ),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_DISCOVERY: True}})
        ).to_be(True)
        await semaphore.acquire()  # Returns after platform setup.
        mock_discovery.assert_called()
        mock_discover_statics.assert_called()
        pywemo_devices.append(create_device(2))

        # Test that discovery runs periodically and the async_dispatcher_send code works.
        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + timedelta(seconds=WemoDiscovery.ADDITIONAL_SECONDS_BETWEEN_SCANS + 1),
        )
        await hass.async_block_till_done()
        # Test that discover_statics runs during discovery
        expect(mock_discover_statics.call_count).to_equal(3)

    entity_entries = list(entity_registry.entities.values())
    expect(len(entity_entries)).to_equal(3)

    await hass.async_stop()
    await hass.async_block_till_done()
