"""Test the cloud assist pipeline."""

from tryke import Depends, fixture, test

from homeassistant.components.cloud.assist_pipeline import (
    async_migrate_cloud_pipeline_engine,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import load_homeassistant

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def migrate_pipeline_invalid_platform(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migrate pipeline with invalid platform."""
    await async_setup_component(hass, "assist_pipeline", {})
    async with expect_raises_async(ValueError):
        await async_migrate_cloud_pipeline_engine(
            hass, Platform.BINARY_SENSOR, "test-engine-id"
        )
