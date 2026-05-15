"""Test the select significant change platform."""

from tryke import Depends, expect, test

from homeassistant.components.select.significant_change import (
    async_check_significant_change,
)
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@test
async def significant_change(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Detect select significant change."""
    attrs1 = {"options": ["option1", "option2"]}
    attrs2 = {"options": ["option1", "option2", "option3"]}

    expect(
        async_check_significant_change(hass, "option1", attrs1, "option1", attrs1)
    ).to_be_falsy()
    expect(
        async_check_significant_change(hass, "option1", attrs1, "option1", attrs2)
    ).to_be_falsy()
    expect(
        async_check_significant_change(hass, "option1", attrs1, "option2", attrs1)
    ).to_be_truthy()
    expect(
        async_check_significant_change(hass, "option1", attrs1, "option2", attrs2)
    ).to_be_truthy()
