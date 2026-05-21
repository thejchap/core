"""Test for the alarm control panel const module."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import alarm_control_panel
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.const import (
    ATTR_CODE,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_CUSTOM_BYPASS,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_ARM_VACATION,
    SERVICE_ALARM_DISARM,
    SERVICE_ALARM_TRIGGER,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import UNDEFINED, UndefinedType

from ._fixtures import setup_mock_alarm_control_panel

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


async def help_test_async_alarm_control_panel_service(
    hass: HomeAssistant,
    entity_id: str,
    service: str,
    code: str | None | UndefinedType = UNDEFINED,
) -> None:
    """Help to call a test alarm control panel service."""
    data: dict[str, Any] = {"entity_id": entity_id}
    if code is not UNDEFINED:
        data[ATTR_CODE] = code

    await hass.services.async_call(
        alarm_control_panel.DOMAIN, service, data, blocking=True
    )
    await hass.async_block_till_done()


@test
async def set_mock_alarm_control_panel_options(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test mock attributes and default code stored in the registry."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(hass)

    entity_registry.async_update_entity_options(
        "alarm_control_panel.test_alarm_control_panel",
        "alarm_control_panel",
        {alarm_control_panel.CONF_DEFAULT_CODE: "1234"},
    )
    await hass.async_block_till_done()

    expect(
        mock_alarm_control_panel_entity._alarm_control_panel_option_default_code
    ).to_equal("1234")
    state = hass.states.get(mock_alarm_control_panel_entity.entity_id)
    expect(state).not_.to_be_none()
    expect(state.attributes["code_format"]).to_equal(CodeFormat.NUMBER)
    expect(state.attributes["supported_features"]).to_equal(
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS
        | AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_VACATION
        | AlarmControlPanelEntityFeature.TRIGGER
    )


@test
async def default_code_option_update(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test default code stored in the registry is updated."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(hass)

    expect(
        mock_alarm_control_panel_entity._alarm_control_panel_option_default_code
    ).to_be_none()

    entity_registry.async_update_entity_options(
        "alarm_control_panel.test_alarm_control_panel",
        "alarm_control_panel",
        {alarm_control_panel.CONF_DEFAULT_CODE: "4321"},
    )
    await hass.async_block_till_done()

    expect(
        mock_alarm_control_panel_entity._alarm_control_panel_option_default_code
    ).to_equal("4321")


@test
async def alarm_control_panel_arm_with_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test alarm control panel entity with open service."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(
        hass,
        code_format=CodeFormat.TEXT,
        supported_features=AlarmControlPanelEntityFeature.ARM_AWAY,
    )

    state = hass.states.get(mock_alarm_control_panel_entity.entity_id)
    expect(state.attributes["code_format"]).to_equal(CodeFormat.TEXT)

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_alarm_control_panel_service(
            hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_AWAY
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_alarm_control_panel_service(
            hass,
            mock_alarm_control_panel_entity.entity_id,
            SERVICE_ALARM_ARM_AWAY,
            code="",
        )
    await help_test_async_alarm_control_panel_service(
        hass,
        mock_alarm_control_panel_entity.entity_id,
        SERVICE_ALARM_ARM_AWAY,
        code="1234",
    )
    expect(mock_alarm_control_panel_entity.calls_arm_away.call_count).to_equal(1)
    mock_alarm_control_panel_entity.calls_arm_away.assert_called_with("1234")


@test
async def alarm_control_panel_with_no_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test alarm control panel entity without code."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(
        hass,
        code_format=CodeFormat.NUMBER,
        code_arm_required=False,
    )

    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_AWAY
    )
    mock_alarm_control_panel_entity.calls_arm_away.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_CUSTOM_BYPASS
    )
    mock_alarm_control_panel_entity.calls_arm_custom.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_HOME
    )
    mock_alarm_control_panel_entity.calls_arm_home.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_NIGHT
    )
    mock_alarm_control_panel_entity.calls_arm_night.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_VACATION
    )
    mock_alarm_control_panel_entity.calls_arm_vacation.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_DISARM
    )
    mock_alarm_control_panel_entity.calls_disarm.assert_called_with(None)
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_TRIGGER
    )
    mock_alarm_control_panel_entity.calls_trigger.assert_called_with(None)


@test
async def alarm_control_panel_with_default_code(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test alarm control panel entity with default code."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(
        hass,
        code_format=CodeFormat.NUMBER,
        code_arm_required=True,
    )

    entity_registry.async_update_entity_options(
        "alarm_control_panel.test_alarm_control_panel",
        "alarm_control_panel",
        {alarm_control_panel.CONF_DEFAULT_CODE: "1234"},
    )
    await hass.async_block_till_done()

    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_AWAY
    )
    mock_alarm_control_panel_entity.calls_arm_away.assert_called_with("1234")
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_CUSTOM_BYPASS
    )
    mock_alarm_control_panel_entity.calls_arm_custom.assert_called_with("1234")
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_HOME
    )
    mock_alarm_control_panel_entity.calls_arm_home.assert_called_with("1234")
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_NIGHT
    )
    mock_alarm_control_panel_entity.calls_arm_night.assert_called_with("1234")
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_ARM_VACATION
    )
    mock_alarm_control_panel_entity.calls_arm_vacation.assert_called_with("1234")
    await help_test_async_alarm_control_panel_service(
        hass, mock_alarm_control_panel_entity.entity_id, SERVICE_ALARM_DISARM
    )
    mock_alarm_control_panel_entity.calls_disarm.assert_called_with("1234")


@test
async def alarm_control_panel_not_log_deprecated_state_warning(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test correctly using alarm_state doesn't log issue or raise repair."""
    mock_alarm_control_panel_entity = await setup_mock_alarm_control_panel(hass)

    state = hass.states.get(mock_alarm_control_panel_entity.entity_id)
    expect(state).not_.to_be_none()
    expect(
        "the 'alarm_state' property and return its state using the AlarmControlPanelState enum"
        in caplog.text
    ).to_be_falsy()
