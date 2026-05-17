"""Tryke fixtures for the switch tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.switch import DOMAIN
from homeassistant.core import HomeAssistant

from tests.components.common import target_entities
from tests.hass_fixtures import hass as hass_fixture


@fixture
def enable_labs_preview_features() -> Generator[None]:
    """Enable labs preview features."""
    with patch(
        "homeassistant.components.labs.async_is_preview_feature_enabled",
        return_value=True,
    ):
        yield


@fixture
async def target_switches(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple switch entities associated with different targets."""
    return await target_entities(hass, DOMAIN)


@fixture
async def target_input_booleans(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[str]]:
    """Create multiple input_boolean entities associated with different targets."""
    return await target_entities(hass, "input_boolean")
