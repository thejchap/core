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
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


async def _expect_raises_async(
    coro_factory, exc_type: type[BaseException], match: str | None = None
) -> None:
    """Async-safe version of expect(...).to_raise() preserving regex match."""
    import re  # noqa: PLC0415

    raised: BaseException | None = None
    try:
        await coro_factory()
    except BaseException as exc:  # noqa: BLE001 - test assertion
        raised = exc
    expect(raised).not_.to_be(None)
    expect(isinstance(raised, exc_type)).to_be_truthy()
    if match is not None:
        candidates = (
            str(raised),
            *(str(a) for a in getattr(raised, "args", ())),
        )
        expect(bool(re.search(match, " ".join(candidates)))).to_be_truthy()


@test.skip("uses syrupy snapshot")
async def switch_entities() -> None:
    """Test switch entities (snapshot platform)."""


@test.cases(
    test.case("away_mode", entity_id="switch.test_system_away_mode", method="set_away_mode"),
    test.case("continuous_fan", entity_id="switch.test_system_continuous_fan", method="set_continuous_mode"),
    test.case("quiet_mode", entity_id="switch.test_system_quiet_mode", method="set_quiet_mode"),
    test.case("turbo_mode", entity_id="switch.test_system_turbo_mode", method="set_turbo_mode"),
)
async def switch_toggles(
    entity_id: str,
    method: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test switch toggles."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.SWITCH]):
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

    await setup_integration(hass, mock_config_entry)

    entity_id = "switch.test_system_turbo_mode"
    expect(hass.states.get(entity_id)).to_be_falsy()
    expect(entity_registry.async_get(entity_id)).to_be_falsy()


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
    entity_id: str,
    method: str,
    service: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: MagicMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error handling when toggling switches."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.SWITCH]):
        await setup_integration(hass, mock_config_entry)

    status = mock_actron_api.state_manager.get_status.return_value
    mock_method = getattr(status.user_aircon_settings, method)
    mock_method.side_effect = ActronAirAPIError("Test error")

    async def call() -> None:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            service,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )

    await _expect_raises_async(call, HomeAssistantError, match="Test error")
