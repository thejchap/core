"""Tests for the AirGradient button platform."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from airgradient import AirGradientConnectionError, AirGradientError, Config
from tryke import Depends, expect, fixture, test

from homeassistant.components.airgradient.const import DOMAIN
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import setup_integration
from ._fixtures import (
    mock_airgradient_client,
    mock_cloud_airgradient_client,
    mock_config_entry,
)

from tests.common import MockConfigEntry, async_fire_time_changed, async_load_fixture
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async, mock_async_zeroconf


_FAKE_TRANSLATIONS = {
    "component.airgradient.entity.button.co2_calibration.name": "Calibrate CO2 sensor",
    "component.airgradient.entity.button.led_bar_test.name": "Test LED bar",
    "component.airgradient.exceptions.communication_error.message": (
        "An error occurred while communicating with the Airgradient device: {error}"
    ),
    "component.airgradient.exceptions.unknown_error.message": (
        "An unknown error occurred while communicating with the Airgradient device: {error}"
    ),
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


def _fake_get_exception_message(
    translation_domain, translation_key, translation_placeholders=None
):
    key = f"component.{translation_domain}.exceptions.{translation_key}.message"
    msg = _FAKE_TRANSLATIONS.get(key, translation_key)
    if translation_placeholders:
        try:
            msg = msg.format(**translation_placeholders)
        except KeyError:
            pass
    return msg


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
        patch(
            "homeassistant.helpers.translation.async_get_exception_message",
            side_effect=_fake_get_exception_message,
        ),
        patch.dict(
            "homeassistant.exceptions._function_cache",
            {"async_get_exception_message": _fake_get_exception_message},
            clear=False,
        ),
    )


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def pressing_button(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test pressing button."""
    p1, p2, p3, p4 = _patch_translations()
    with p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {
                ATTR_ENTITY_ID: "button.airgradient_calibrate_co2_sensor",
            },
            blocking=True,
        )
        mock_airgradient_client.request_co2_calibration.assert_called_once()

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {
                ATTR_ENTITY_ID: "button.airgradient_test_led_bar",
            },
            blocking=True,
        )
        mock_airgradient_client.request_led_bar_test.assert_called_once()


@test
async def cloud_creates_no_button(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cloud_airgradient_client: AsyncMock = Depends(mock_cloud_airgradient_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test cloud configuration control."""
    with patch("homeassistant.components.airgradient.PLATFORMS", [Platform.BUTTON]):
        await setup_integration(hass, mock_config_entry)

    expect(len(hass.states.async_all())).to_equal(0)

    mock_cloud_airgradient_client.get_config.return_value = Config.from_json(
        await async_load_fixture(hass, "get_config_local.json", DOMAIN)
    )

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(2)

    mock_cloud_airgradient_client.get_config.return_value = Config.from_json(
        await async_load_fixture(hass, "get_config_cloud.json", DOMAIN)
    )

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)


@test.cases(
    test.case(
        "connection_error",
        exception=AirGradientConnectionError("Something happened"),
        error_message="An error occurred while communicating with the Airgradient device: Something happened",
    ),
    test.case(
        "general_error",
        exception=AirGradientError("Something else happened"),
        error_message="An unknown error occurred while communicating with the Airgradient device: Something else happened",
    ),
)
async def exception_handling(
    exception: Exception,
    error_message: str,
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_airgradient_client: AsyncMock = Depends(mock_airgradient_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test exception handling."""
    p1, p2, p3, p4 = _patch_translations()
    with p1, p2, p3, p4:
        await setup_integration(hass, mock_config_entry)
        mock_airgradient_client.request_co2_calibration.side_effect = exception
        async with expect_raises_async(HomeAssistantError, match=error_message):
            await hass.services.async_call(
                BUTTON_DOMAIN,
                SERVICE_PRESS,
                {
                    ATTR_ENTITY_ID: "button.airgradient_calibrate_co2_sensor",
                },
                blocking=True,
            )


@test.skip("uses syrupy snapshot + parametrized airgradient_devices")
async def all_entities() -> None:
    """Stub: snapshot + parametrized airgradient_devices."""
