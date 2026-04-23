"""Tryke fixtures for Flexit Nordic (BACnet)."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from flexit_bacnet import FlexitBACnet
from tryke import Depends, expect, fixture

from homeassistant import config_entries
from homeassistant.components.flexit_bacnet.const import DOMAIN
from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def flow_id(hass: HomeAssistant = Depends(hass_fixture)) -> str:
    """Return initial ID for user-initiated configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    return result["flow_id"]


@fixture
def mock_flexit_bacnet() -> Generator[AsyncMock]:
    """Mock data from the device."""
    flexit_bacnet = AsyncMock(spec=FlexitBACnet)
    with (
        patch(
            "homeassistant.components.flexit_bacnet.config_flow.FlexitBACnet",
            return_value=flexit_bacnet,
        ),
        patch(
            "homeassistant.components.flexit_bacnet.coordinator.FlexitBACnet",
            return_value=flexit_bacnet,
        ),
    ):
        flexit_bacnet.serial_number = "0000-0001"
        flexit_bacnet.device_name = "Device Name"
        flexit_bacnet.model = "S4 RER"
        yield flexit_bacnet


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.flexit_bacnet.async_setup_entry", return_value=True
    ) as setup_entry_mock:
        yield setup_entry_mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_IP_ADDRESS: "1.1.1.1",
            CONF_DEVICE_ID: 2,
        },
        unique_id="0000-0001",
    )
