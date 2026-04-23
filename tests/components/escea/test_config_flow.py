"""Tests for Escea."""

from collections.abc import Callable, Coroutine
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.escea.const import DOMAIN, ESCEA_FIREPLACE
from homeassistant.components.escea.discovery import DiscoveryServiceListener
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_discovery_service() -> AsyncMock:
    """Mock discovery service."""
    discovery_service = AsyncMock()
    discovery_service.controllers = {}
    return discovery_service


@fixture
def mock_controller() -> MagicMock:
    """Mock controller."""
    return MagicMock()


def _mock_start_discovery(
    discovery_service: MagicMock, controller: MagicMock
) -> Callable[[], Coroutine[None, None, None]]:
    """Mock start discovery service."""

    async def do_discovered() -> None:
        """Call the listener callback."""
        listener: DiscoveryServiceListener = discovery_service.call_args[0][0]
        listener.controller_discovered(controller)

    return do_discovered


@test
async def not_found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_discovery_service: AsyncMock = Depends(mock_discovery_service),
) -> None:
    """Test not finding any Escea controllers."""
    with (
        patch(
            "homeassistant.components.escea.discovery.pescea_discovery_service"
        ) as discovery_service,
        patch("homeassistant.components.escea.config_flow.TIMEOUT_DISCOVERY", 0),
    ):
        discovery_service.return_value = mock_discovery_service

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_devices_found")
    expect(discovery_service.return_value.close.call_count).to_equal(1)


@test
async def found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_controller: MagicMock = Depends(mock_controller),
    mock_discovery_service: AsyncMock = Depends(mock_discovery_service),
) -> None:
    """Test finding an Escea controller."""
    mock_discovery_service.controllers["test-uid"] = mock_controller

    with (
        patch(
            "homeassistant.components.escea.async_setup_entry",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.escea.discovery.pescea_discovery_service"
        ) as discovery_service,
    ):
        discovery_service.return_value = mock_discovery_service
        mock_discovery_service.start_discovery.side_effect = _mock_start_discovery(
            discovery_service, mock_controller
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(mock_setup.call_count).to_equal(1)


@test
async def single_instance_allowed(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
) -> None:
    """Test single instance allowed."""
    config_entry = MockConfigEntry(domain=DOMAIN, title=ESCEA_FIREPLACE)
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.escea.discovery.pescea_discovery_service"
    ) as discovery_service:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("single_instance_allowed")
    expect(discovery_service.call_count).to_equal(0)
