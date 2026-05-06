"""Tests for the Abode lock device."""

import json
from unittest.mock import patch

from jaraco.abode.helpers import urls as URL
import requests_mock as requests_mock_lib
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN, LockState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

DEVICE_ID = "lock.test_lock"


@fixture
def _abode_setup(
    _requests: requests_mock_lib.Mocker = Depends(requests_mock_fixture),
) -> requests_mock_lib.Mocker:
    """Wire the autouse Abode HTTP mocks for tryke and expose the mocker."""
    return _requests


@test
async def entity_registry(
    _trigger: requests_mock_lib.Mocker = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, LOCK_DOMAIN)

    entry = entity_registry.async_get(DEVICE_ID)
    expect(entry.unique_id).to_equal("51cab3b545d2o34ed7fz02731bda5324")


@test
async def attributes(
    _trigger: requests_mock_lib.Mocker = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the lock attributes are correct."""
    await setup_platform(hass, LOCK_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state.state).to_equal(LockState.LOCKED)
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("ZW:00000004")
    expect(state.attributes.get("battery_low")).to_be_falsy()
    expect(state.attributes.get("no_response")).to_be_falsy()
    expect(state.attributes.get("device_type")).to_equal("Door Lock")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Test Lock")


@test
async def lock(
    _trigger: requests_mock_lib.Mocker = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the lock can be locked."""
    await setup_platform(hass, LOCK_DOMAIN)

    with patch("jaraco.abode.devices.lock.Lock.lock") as mock_lock:
        await hass.services.async_call(
            LOCK_DOMAIN, SERVICE_LOCK, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_lock.assert_called_once()


@test
async def unlock(
    _trigger: requests_mock_lib.Mocker = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the lock can be unlocked."""
    await setup_platform(hass, LOCK_DOMAIN)

    with patch("jaraco.abode.devices.lock.Lock.unlock") as mock_unlock:
        await hass.services.async_call(
            LOCK_DOMAIN, SERVICE_UNLOCK, {ATTR_ENTITY_ID: DEVICE_ID}, blocking=True
        )
        await hass.async_block_till_done()
        mock_unlock.assert_called_once()


@test
async def retrofit_lock_discovered(
    requests_mock: requests_mock_lib.Mocker = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test retrofit locks are discovered as lock entities."""
    devices = json.loads(await async_load_fixture(hass, "devices.json", "abode"))
    for device in devices:
        if device["type_tag"] == "device_type.door_lock":
            device["type_tag"] = "device_type.retrofit_lock"
            device["type"] = "Retrofit Lock"
            break

    requests_mock.get(URL.DEVICES, text=json.dumps(devices))

    await setup_platform(hass, LOCK_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.LOCKED)
