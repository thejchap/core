"""Tests for iZone."""

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.izone.const import DISPATCH_CONTROLLER_DISCOVERED, IZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.dispatcher import async_dispatcher_send

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@fixture
def mock_disco() -> Mock:
    """Mock discovery service."""
    disco = Mock()
    disco.pi_disco = Mock()
    disco.pi_disco.controllers = {}
    return disco


def _mock_start_discovery(hass: HomeAssistant, mock_disco: Mock) -> Callable[..., Mock]:
    def do_disovered(*args: Any) -> Mock:
        async_dispatcher_send(hass, DISPATCH_CONTROLLER_DISCOVERED, True)
        return mock_disco

    return do_disovered


@test
async def not_found(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_disco: Mock = Depends(mock_disco),
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
        start_disco.side_effect = _mock_start_discovery(hass, mock_disco)
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
    hass: HomeAssistant = Depends(hass_fixture),
    mock_disco: Mock = Depends(mock_disco),
) -> None:
    """Test finding iZone controller."""
    mock_disco.pi_disco.controllers["blah"] = object()

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
        start_disco.side_effect = _mock_start_discovery(hass, mock_disco)
        result = await hass.config_entries.flow.async_init(
            IZONE, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

    mock_setup.assert_called_once()
