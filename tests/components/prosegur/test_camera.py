"""The camera tests for the prosegur platform."""

import logging
from unittest.mock import AsyncMock, MagicMock

from pyprosegur.exceptions import ProsegurException
from tryke import Depends, expect, fixture, test

from homeassistant.components import camera
from homeassistant.components.camera import Image
from homeassistant.components.prosegur.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import (
    init_integration as init_integration_fixture,
    mock_install as mock_install_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def cam(
    hass: HomeAssistant = Depends(_trigger_executor),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test prosegur get_image."""
    image = await camera.async_get_image(hass, "camera.contract_1234abcd_test_cam")
    expect(image).to_equal(Image(content_type="image/jpeg", content=b"ABC"))


@test
async def cam_fail(
    hass: HomeAssistant = Depends(_trigger_executor),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
    mock_install: MagicMock = Depends(mock_install_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test prosegur get_image fails."""
    mock_install.get_image = AsyncMock(
        return_value=b"ABC", side_effect=ProsegurException()
    )

    caplog.set_level(logging.ERROR, logger="homeassistant.components.prosegur")
    async with expect_raises_async(HomeAssistantError, match="Unable to get image"):
        await camera.async_get_image(hass, "camera.contract_1234abcd_test_cam")

    expect("Image test_cam doesn't exist" in caplog.text).to_be(True)


@test
async def request_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
    mock_install: MagicMock = Depends(mock_install_fixture),
) -> None:
    """Test the camera request image service."""
    await hass.services.async_call(
        DOMAIN,
        "request_image",
        {ATTR_ENTITY_ID: "camera.contract_1234abcd_test_cam"},
    )
    await hass.async_block_till_done()

    expect(bool(mock_install.request_image.called)).to_be(True)


@test
async def request_image_fail(
    hass: HomeAssistant = Depends(_trigger_executor),
    _init_integration: MockConfigEntry = Depends(init_integration_fixture),
    mock_install: MagicMock = Depends(mock_install_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the camera request image service fails."""
    mock_install.request_image = AsyncMock(side_effect=ProsegurException())

    caplog.set_level(logging.ERROR, logger="homeassistant.components.prosegur")
    await hass.services.async_call(
        DOMAIN,
        "request_image",
        {ATTR_ENTITY_ID: "camera.contract_1234abcd_test_cam"},
    )
    await hass.async_block_till_done()

    expect(bool(mock_install.request_image.called)).to_be(True)
    expect("Could not request image from camera test_cam" in caplog.text).to_be(True)
