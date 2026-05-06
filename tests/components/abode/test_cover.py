"""Tests for the Abode cover device."""

from unittest.mock import patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode import ATTR_DEVICE_ID
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN, CoverState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

DEVICE_ID = "cover.garage_door"


@fixture
def _abode_setup(
    _requests: requests_mock.Mocker = Depends(requests_mock_fixture),
) -> None:
    """Wire the autouse Abode HTTP mocks for tryke."""


@test
async def entity_registry(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the devices are registered in the entity registry."""
    await setup_platform(hass, COVER_DOMAIN)

    entry = entity_registry.async_get(DEVICE_ID)
    expect(entry.unique_id).to_equal("61cbz3b542d2o33ed2fz02721bda3324")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the cover attributes are correct."""
    await setup_platform(hass, COVER_DOMAIN)

    state = hass.states.get(DEVICE_ID)
    expect(state.state).to_equal(CoverState.CLOSED)
    expect(state.attributes.get(ATTR_DEVICE_ID)).to_equal("ZW:00000007")
    expect(state.attributes.get("battery_low")).to_be_falsy()
    expect(state.attributes.get("no_response")).to_be_falsy()
    expect(state.attributes.get("device_type")).to_equal("Secure Barrier")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Garage Door")


@test
async def open_cover(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the cover can be opened."""
    await setup_platform(hass, COVER_DOMAIN)

    with patch("jaraco.abode.devices.cover.Cover.open_cover") as mock_open:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: DEVICE_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_open.assert_called_once()


@test
async def close_cover(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the cover can be closed."""
    await setup_platform(hass, COVER_DOMAIN)

    with patch("jaraco.abode.devices.cover.Cover.close_cover") as mock_close:
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: DEVICE_ID},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_close.assert_called_once()
