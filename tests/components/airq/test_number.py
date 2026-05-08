"""Test the NUMBER platform from air-Q integration."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from . import setup_platform
from ._fixtures import mock_airq
from .common import TEST_BRIGHTNESS, TEST_DEVICE_INFO

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async, mock_async_zeroconf

ENTITY_ID = f"number.{TEST_DEVICE_INFO['name']}_led_brightness"


_FAKE_TRANSLATIONS = {
    "component.airq.entity.number.airq_led_brightness.name": "LED brightness",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


def _patch_translations():
    return (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    )


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test.cases(
    test.case("zero", new_brightness=0),
    test.case("hundred", new_brightness=100),
    test.case("rotate", new_brightness=(TEST_BRIGHTNESS + 10) % 100),
)
async def number_set_value(
    new_brightness: int,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that setting value works."""
    p1, p2 = _patch_translations()
    with p1, p2:
        await setup_platform(hass, Platform.NUMBER)

        state = hass.states.get(ENTITY_ID)
        expect(state).not_.to_be(None)
        expect(float(state.state)).to_equal(float(TEST_BRIGHTNESS))

        mock_airq.get_current_brightness.return_value = new_brightness

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": ENTITY_ID, "value": new_brightness},
            blocking=True,
        )
        await hass.async_block_till_done()

        mock_airq.set_current_brightness.assert_called_once_with(new_brightness)

        state = hass.states.get(ENTITY_ID)
        expect(state).not_.to_be(None)
        expect(float(state.state)).to_equal(float(new_brightness))


@test.cases(
    test.case("negative", new_brightness=-1),
    test.case("over_max", new_brightness=110),
)
async def number_set_invalid_value_caught_by_hass(
    new_brightness: int,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that setting incorrect values errors."""
    p1, p2 = _patch_translations()
    with p1, p2:
        await setup_platform(hass, Platform.NUMBER)

        async with expect_raises_async(ServiceValidationError):
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": ENTITY_ID, "value": new_brightness},
                blocking=True,
            )

        mock_airq.set_current_brightness.assert_not_called()
