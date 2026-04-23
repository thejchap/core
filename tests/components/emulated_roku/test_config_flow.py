"""Tests for emulated_roku config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.emulated_roku import config_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.emulated_roku._fixtures import mock_setup_entry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def flow_works(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that config flow works."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"name": "Emulated Roku Test", "listen_port": 8060},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Emulated Roku Test")
    expect(result.get("data")).to_equal({"name": "Emulated Roku Test", "listen_port": 8060})


@test
async def flow_already_registered_entry(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that config flow doesn't allow existing names."""
    MockConfigEntry(
        domain="emulated_roku",
        data={"name": "Emulated Roku Test", "listen_port": 8062},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={"name": "Emulated Roku Test", "listen_port": 8062},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
