"""Fixtures for Sighthound tests."""

from collections.abc import Generator
import datetime
from unittest import mock

from PIL import UnidentifiedImageError
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

MOCK_DETECTIONS = {
    "image": {"width": 960, "height": 480, "orientation": 1},
    "objects": [
        {
            "type": "person",
            "boundingBox": {"x": 227, "y": 133, "height": 245, "width": 125},
        },
        {
            "type": "person",
            "boundingBox": {"x": 833, "y": 137, "height": 268, "width": 93},
        },
    ],
    "requestId": "545cec700eac4d389743e2266264e84b",
}

MOCK_NOW = datetime.datetime(2020, 2, 20, 10, 5, 3)


@fixture
async def setup_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Set up the homeassistant integration."""
    await async_setup_component(hass, "homeassistant", {})
    return hass


@fixture
def mock_detections() -> Generator[mock.MagicMock]:
    """Return a mock detection."""
    with mock.patch(
        "simplehound.core.cloud.detect", return_value=MOCK_DETECTIONS
    ) as detection:
        yield detection


@fixture
def mock_image() -> Generator[mock.MagicMock]:
    """Return a mock camera image."""
    with mock.patch(
        "homeassistant.components.demo.camera.DemoCamera.camera_image",
        return_value=b"Test",
    ) as image:
        yield image


@fixture
def mock_bad_image_data() -> Generator[mock.MagicMock]:
    """Mock bad image data."""
    with mock.patch(
        "homeassistant.components.sighthound.image_processing.Image.open",
        side_effect=UnidentifiedImageError,
    ) as bad_data:
        yield bad_data


@fixture
def mock_now() -> Generator[mock.MagicMock]:
    """Return a mock now datetime."""
    with mock.patch("homeassistant.util.dt.now", return_value=MOCK_NOW) as now_dt:
        yield now_dt
