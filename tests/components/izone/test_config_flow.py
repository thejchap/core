"""Tests for iZone."""

from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.izone.const import DISPATCH_CONTROLLER_DISCOVERED, IZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ._fixtures import mock_disco

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(_disco: Mock = Depends(mock_disco)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _mock_start_discovery(hass: HomeAssistant, disco: Mock) -> Callable[..., Mock]:
    def do_disovered(*args: Any) -> Mock:
        async_dispatcher_send(hass, DISPATCH_CONTROLLER_DISCOVERED, True)
        return disco

    return do_disovered


@test
async def not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    disco: Mock = Depends(mock_disco),
) -> None:
    """Test not finding iZone controller."""
    with (
        patch(
            "homeassistant.components.izone.config_flow.async_start_discovery_service"
        ) as start_disco,
        patch(
            "homeassistant.components.izone.config_flow.async_stop_discovery_service",
            return_value=None,
        ) as stop_disco,
    ):
        start_disco.side_effect = _mock_start_discovery(hass, disco)
        result = await hass.config_entries.flow.async_init(
            IZONE, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.ABORT)

        await hass.async_block_till_done()

    stop_disco.assert_called_once()


@test
async def found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    disco: Mock = Depends(mock_disco),
) -> None:
    """Test finding iZone controller."""
    disco.pi_disco.controllers["blah"] = object()

    with (
        patch(
            "homeassistant.components.izone.climate.async_setup_entry",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.izone.config_flow.async_start_discovery_service"
        ) as start_disco,
        patch(
            "homeassistant.components.izone.async_start_discovery_service",
            return_value=None,
        ),
    ):
        start_disco.side_effect = _mock_start_discovery(hass, disco)
        result = await hass.config_entries.flow.async_init(
            IZONE, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

    mock_setup.assert_called_once()
