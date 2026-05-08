"""Test Scrape component setup process."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.scrape.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from . import MockRestData, return_integration_config

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Force tryke to fully resolve hass before each test."""


@test
async def setup_config_no_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test setup from yaml missing configuration options."""
    config = {DOMAIN: None}

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect(entity_registry.entities).to_equal({})


@test
async def setup_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup from yaml."""
    config = {
        DOMAIN: [
            return_integration_config(
                sensors=[{"select": ".current-version h1", "name": "HA version"}]
            )
        ]
    }

    mocker = MockRestData("test_scrape_sensor")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ) as mock_setup:
        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.ha_version")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("Current Version: 2021.12.10")
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test.skip("requires freezegun + recovery flow - port deferred")
async def setup_no_data_fails_with_recovery() -> None:
    """Stub for test_setup_no_data_fails_with_recovery (port deferred)."""

@test.skip("requires complex log capture - port deferred")
async def setup_config_no_sensors() -> None:
    """Stub for test_setup_config_no_sensors (port deferred)."""

@test.skip("requires config_entry setup - port deferred")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("requires config_entry setup - port deferred")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("requires device_registry setup - port deferred")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices (port deferred)."""

@test.skip("requires template eval - port deferred")
async def resource_template() -> None:
    """Stub for test_resource_template (port deferred)."""

@test.skip("requires migration scaffolding - port deferred")
async def migrate_from_future() -> None:
    """Stub for test_migrate_from_future (port deferred)."""

@test.skip("requires migration scaffolding - port deferred")
async def migrate_from_version_1_to_2() -> None:
    """Stub for test_migrate_from_version_1_to_2 (port deferred)."""
