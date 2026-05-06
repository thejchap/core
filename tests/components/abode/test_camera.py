"""Tests for the Abode camera device."""

from unittest.mock import patch

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.abode.const import DOMAIN
from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN, CameraState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import requests_mock_fixture
from .common import setup_platform

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


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
    await setup_platform(hass, CAMERA_DOMAIN)

    entry = entity_registry.async_get("camera.test_cam")
    expect(entry.unique_id).to_equal("d0a3a1c316891ceb00c20118aae2a133")


@test
async def attributes(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the camera attributes are correct."""
    await setup_platform(hass, CAMERA_DOMAIN)

    state = hass.states.get("camera.test_cam")
    expect(state.state).to_equal(CameraState.IDLE)


@test
async def capture_image(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the camera capture image service."""
    await setup_platform(hass, CAMERA_DOMAIN)

    with patch("jaraco.abode.devices.camera.Camera.capture") as mock_capture:
        await hass.services.async_call(
            DOMAIN,
            "capture_image",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_capture.assert_called_once()


@test
async def camera_on(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the camera turn on service."""
    await setup_platform(hass, CAMERA_DOMAIN)

    with patch("jaraco.abode.devices.camera.Camera.privacy_mode") as mock_capture:
        await hass.services.async_call(
            CAMERA_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_capture.assert_called_once_with(False)


@test
async def camera_off(
    _trigger: None = Depends(_abode_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the camera turn off service."""
    await setup_platform(hass, CAMERA_DOMAIN)

    with patch("jaraco.abode.devices.camera.Camera.privacy_mode") as mock_capture:
        await hass.services.async_call(
            CAMERA_DOMAIN,
            "turn_off",
            {ATTR_ENTITY_ID: "camera.test_cam"},
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_capture.assert_called_once_with(True)
