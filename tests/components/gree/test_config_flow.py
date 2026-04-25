"""Tests for the Gree Integration."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.gree.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import device, discovery, mock_setup_entry
from .common import FakeDiscovery

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _discovery: object = Depends(discovery),
    _device: object = Depends(device),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def creating_entry_sets_up_climate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test setting up Gree creates the climate components."""
    with (
        patch("homeassistant.components.gree.config_flow.DISCOVERY_TIMEOUT", 0),
        patch(
            "homeassistant.components.gree.config_flow.Discovery",
            return_value=FakeDiscovery(),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

        expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def creating_entry_has_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test setting up Gree without devices aborts."""
    with (
        patch("homeassistant.components.gree.config_flow.DISCOVERY_TIMEOUT", 0),
        patch(
            "homeassistant.components.gree.config_flow.Discovery",
            return_value=FakeDiscovery(),
        ) as flow_discovery,
    ):
        flow_discovery.return_value.mock_devices = []

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.ABORT)

        await hass.async_block_till_done()

        expect(len(setup_entry.mock_calls)).to_equal(0)
