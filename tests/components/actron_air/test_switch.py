"""Tests for the Actron Air switch platform."""

from unittest.mock import MagicMock, patch

from actron_neo_api import ActronAirAPIError
from tryke import Depends, expect, fixture, test

from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import setup_integration
from ._fixtures import mock_actron_api, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


# Inject actron_air switch translations so entity_id slugs include
# "_away_mode", etc. Without this the slug falls back to bare device name.
_FAKE_TRANSLATIONS = {
    "component.actron_air.entity.switch.away_mode.name": "Away mode",
    "component.actron_air.entity.switch.continuous_fan.name": "Continuous fan",
    "component.actron_air.entity.switch.quiet_mode.name": "Quiet mode",
    "component.actron_air.entity.switch.turbo_mode.name": "Turbo mode",
    "component.actron_air.exceptions.api_error.message": (
        "Failed to communicate with Actron Air device: {error}"
    ),
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    if integrations and "actron_air" in integrations:
        return _FAKE_TRANSLATIONS
    return {}


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    """Return the same fake bundle for cached translation lookups."""
    return _FAKE_TRANSLATIONS


def _fake_get_exception_message(
    translation_domain, translation_key, translation_placeholders=None
):
    """Resolve api_error.message manually since translation cache is empty."""
    key = (
        f"component.{translation_domain}.exceptions.{translation_key}.message"
    )
    message = _FAKE_TRANSLATIONS.get(key, translation_key)
    if translation_placeholders:
        try:
            message = message.format(**translation_placeholders)
        except KeyError:
            pass
    return message


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke to build a per-module HookExecutor for this file."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def switch_entities() -> None:
    """Stub for test_switch_entities (snapshot-based)."""


@test.cases(
    test.case(
        "away_mode", entity_id="switch.test_system_away_mode", method="set_away_mode"
    ),
    test.case(
        "continuous_fan",
        entity_id="switch.test_system_continuous_fan",
        method="set_continuous_mode",
    ),
    test.case(
        "quiet_mode",
        entity_id="switch.test_system_quiet_mode",
        method="set_quiet_mode",
    ),
    test.case(
        "turbo_mode",
        entity_id="switch.test_system_turbo_mode",
        method="set_turbo_mode",
    ),
)
async def switch_toggles(
    *,
    entity_id: str,
    method: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test switch toggles."""
    with (
        patch("homeassistant.components.actron_air.PLATFORMS", [Platform.SWITCH]),
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
    ):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value
    mock_method = getattr(status.user_aircon_settings, method)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_method.assert_awaited_once_with(True)
    mock_method.reset_mock()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: [entity_id]},
        blocking=True,
    )
    mock_method.assert_awaited_once_with(False)


@test
async def turbo_mode_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test turbo mode switch is not created when not supported."""
    status = mock_actron_api.state_manager.get_status.return_value
    status.user_aircon_settings.turbo_mode_enabled = {
        "Enabled": False,
        "Supported": False,
    }

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        side_effect=_fake_get_translations,
    ):
        await setup_integration(hass, mock_config_entry)

    entity_id = "switch.test_system_turbo_mode"
    expect(hass.states.get(entity_id) is None).to_be(True)
    expect(entity_registry.async_get(entity_id) is None).to_be(True)


@test.cases(
    test.case(
        "away_mode_on",
        entity_id="switch.test_system_away_mode",
        method="set_away_mode",
        service=SERVICE_TURN_ON,
    ),
    test.case(
        "continuous_fan_off",
        entity_id="switch.test_system_continuous_fan",
        method="set_continuous_mode",
        service=SERVICE_TURN_OFF,
    ),
    test.case(
        "quiet_mode_on",
        entity_id="switch.test_system_quiet_mode",
        method="set_quiet_mode",
        service=SERVICE_TURN_ON,
    ),
    test.case(
        "turbo_mode_off",
        entity_id="switch.test_system_turbo_mode",
        method="set_turbo_mode",
        service=SERVICE_TURN_OFF,
    ),
)
async def switch_api_error(
    *,
    entity_id: str,
    method: str,
    service: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error handling when toggling switches."""
    with (
        patch("homeassistant.components.actron_air.PLATFORMS", [Platform.SWITCH]),
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
    ):
        await setup_integration(hass, mock_config_entry)

        status = mock_actron_api.state_manager.get_status.return_value
        mock_method = getattr(status.user_aircon_settings, method)
        mock_method.side_effect = ActronAirAPIError("Test error")

        raised: HomeAssistantError | None = None
        try:
            await hass.services.async_call(
                SWITCH_DOMAIN,
                service,
                {ATTR_ENTITY_ID: [entity_id]},
                blocking=True,
            )
        except HomeAssistantError as err:
            # str(err) inside the patch context to materialize the
            # translated message via _fake_get_exception_message.
            err._message = str(err)  # noqa: SLF001
            raised = err

    expect(raised is not None).to_be(True)
    expect("Test error" in str(raised)).to_be(True)
