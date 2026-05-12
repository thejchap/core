"""Tests for the lifx component."""

from datetime import timedelta
import socket
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import lifx
from homeassistant.components.lifx import DOMAIN, discovery
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import (
    IP_ADDRESS,
    SERIAL,
    MockFailingLifxCommand,
    _mocked_bulb,
    _mocked_failing_bulb,
    _patch_config_flow_try_connect,
    _patch_device,
    _patch_discovery,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def configuring_lifx_causes_discovery(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that specifying empty config does discovery."""
    start_calls = 0

    class MockLifxDiscovery:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            discovered = _mocked_bulb()
            self.lights = {discovered.mac_addr: discovered}

        def start(self) -> None:
            nonlocal start_calls
            start_calls += 1

        def cleanup(self) -> None:
            pass

    with (
        _patch_config_flow_try_connect(),
        patch.object(discovery, "DEFAULT_TIMEOUT", 0),
        patch(
            "homeassistant.components.lifx.discovery.LifxDiscovery", MockLifxDiscovery
        ),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(start_calls).to_equal(0)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        expect(start_calls).to_equal(1)

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(start_calls).to_equal(2)

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=15))
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(start_calls).to_equal(3)

        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=30))
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(start_calls).to_equal(4)


@test
async def config_entry_reload(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that a config entry can be reloaded."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    with _patch_discovery(), _patch_config_flow_try_connect(), _patch_device():
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(already_migrated_config_entry.state).to_be(ConfigEntryState.LOADED)
        await hass.config_entries.async_unload(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()
        expect(already_migrated_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_retry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that a config entry can be retried."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    with (
        _patch_discovery(no_device=True),
        _patch_config_flow_try_connect(no_device=True),
        _patch_device(no_device=True),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(already_migrated_config_entry.state).to_be(
            ConfigEntryState.SETUP_RETRY
        )


@test
async def get_version_fails(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle get version failing."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    bulb.product = None
    bulb.host_firmware_version = None
    bulb.get_version = MockFailingLifxCommand(bulb)

    with _patch_discovery(device=bulb), _patch_device(device=bulb):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(already_migrated_config_entry.state).to_be(
            ConfigEntryState.SETUP_RETRY
        )


@test
async def dns_error_at_startup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle a DNS error at startup."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: IP_ADDRESS}, unique_id=SERIAL
    )
    already_migrated_config_entry.add_to_hass(hass)
    bulb = _mocked_failing_bulb()

    class MockLifxConnectonDnsError:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.device = bulb

        async def async_setup(self) -> None:
            raise socket.gaierror

        def async_stop(self) -> None:
            pass

    with (
        _patch_discovery(device=bulb),
        patch(
            "homeassistant.components.lifx.LIFXConnection",
            MockLifxConnectonDnsError,
        ),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()
        expect(already_migrated_config_entry.state).to_be(
            ConfigEntryState.SETUP_RETRY
        )


@test.skip("times out under tryke worker due to lifx connection waits")
async def config_entry_wrong_serial() -> None:
    """Test config entry enters setup retry when serial mismatches."""
