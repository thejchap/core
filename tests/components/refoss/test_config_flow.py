"""Tests for the refoss Integration."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.refoss.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.refoss import FakeDiscovery, build_base_device_mock
from tests.components.refoss._fixtures import mock_setup_entry
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def creating_entry_sets_up(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test setting up refoss."""
    with (
        patch("homeassistant.components.refoss.config_flow.DISCOVERY_TIMEOUT", 0),
        patch(
            "homeassistant.components.refoss.util.Discovery",
            return_value=FakeDiscovery(),
        ),
        patch(
            "homeassistant.components.refoss.bridge.async_build_base_device",
            return_value=build_base_device_mock(),
        ),
        patch(
            "homeassistant.components.refoss.switch.isinstance",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def creating_entry_has_no_devices(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test setting up Refoss no devices."""
    with (
        patch("homeassistant.components.refoss.config_flow.DISCOVERY_TIMEOUT", 0),
        patch(
            "homeassistant.components.refoss.util.Discovery",
            return_value=FakeDiscovery(),
        ) as discovery,
    ):
        discovery.return_value.mock_devices = {}

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.ABORT)

        await hass.async_block_till_done()

        expect(len(mock_setup_entry.mock_calls)).to_equal(0)
