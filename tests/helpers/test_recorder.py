"""The tests for the recorder helpers."""

from unittest.mock import patch

from tryke import Depends, expect, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import recorder

from tests.hass_fixtures import hass


@test
async def async_migration_in_progress(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_migration_in_progress wraps the recorder."""
    with patch(
        "homeassistant.components.recorder.util.async_migration_in_progress",
        return_value=False,
    ):
        expect(recorder.async_migration_in_progress(hass)).to_be(False)

    with patch(
        "homeassistant.components.recorder.util.async_migration_in_progress",
        return_value=True,
    ):
        expect(recorder.async_migration_in_progress(hass)).to_be(True)


@test
async def async_migration_is_live(hass: HomeAssistant = Depends(hass)) -> None:
    """Test async_migration_in_progress wraps the recorder."""
    with patch(
        "homeassistant.components.recorder.util.async_migration_is_live",
        return_value=False,
    ):
        expect(recorder.async_migration_is_live(hass)).to_be(False)

    with patch(
        "homeassistant.components.recorder.util.async_migration_is_live",
        return_value=True,
    ):
        expect(recorder.async_migration_is_live(hass)).to_be(True)
