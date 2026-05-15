"""Tryke fixtures for image tests."""

from tryke import Depends, fixture

from homeassistant.components import image
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import MockModule, mock_integration, mock_platform
from tests.hass_fixtures import hass as hass_fixture


class MockImageEntity(image.ImageEntity):
    """Mock image entity."""

    _attr_name = "Test"

    async def async_added_to_hass(self) -> None:
        """Set the update time."""
        self._attr_image_last_updated = dt_util.utcnow()

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        return b"Test"


class MockImagePlatform:
    """A mock image platform."""

    PLATFORM_SCHEMA = image.PLATFORM_SCHEMA

    def __init__(self, entities: list[image.ImageEntity]) -> None:
        """Initialize."""
        self._entities = entities

    async def async_setup_platform(
        self,
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up the mock image platform."""
        async_add_entities(self._entities)


@fixture
async def mock_image_platform(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Initialize a mock image platform."""
    mock_integration(hass, MockModule(domain="test"))
    mock_platform(hass, "test.image", MockImagePlatform([MockImageEntity(hass)]))
    assert await async_setup_component(
        hass, image.DOMAIN, {"image": {"platform": "test"}}
    )
    await hass.async_block_till_done()


@fixture
async def setup_media_source(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up media source."""
    assert await async_setup_component(hass, "media_source", {})
