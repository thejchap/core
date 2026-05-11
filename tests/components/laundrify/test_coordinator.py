"""Test the laundrify coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
from laundrify_aio import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.laundrify.const import DEFAULT_POLL_INTERVAL, DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import laundrify_api_mock, laundrify_config_entry

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

# Device ID from fixtures/machines.json
DEVICE_ID = "14"


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def coordinator_update_success(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the coordinator update is performed successfully."""
    freezer.tick(timedelta(seconds=DEFAULT_POLL_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{DEVICE_ID}_{SensorDeviceClass.ENERGY}"
    )
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state != STATE_UNAVAILABLE).to_be(True)


@test
async def coordinator_update_unauthorized(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
    laundrify_api_mock: AsyncMock = Depends(laundrify_api_mock),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the coordinator update fails if an UnauthorizedException is thrown."""
    laundrify_api_mock.get_machines.side_effect = exceptions.UnauthorizedException

    freezer.tick(timedelta(seconds=DEFAULT_POLL_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{DEVICE_ID}_{SensorDeviceClass.ENERGY}"
    )
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def coordinator_update_connection_failed(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    laundrify_config_entry: MockConfigEntry = Depends(laundrify_config_entry),
    laundrify_api_mock: AsyncMock = Depends(laundrify_api_mock),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the coordinator update fails if an ApiConnectionException is thrown."""
    laundrify_api_mock.get_machines.side_effect = exceptions.ApiConnectionException

    freezer.tick(timedelta(seconds=DEFAULT_POLL_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{DEVICE_ID}_{SensorDeviceClass.ENERGY}"
    )
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
