"""Test the Radio Browser config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.radio_browser.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.radio_browser._fixtures import mock_config_entry, mock_setup_entry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Radio Browser")
    expect(result2.get("data")).to_equal({})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort if the Radio Browser is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def onboarding_flow(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the onboarding configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "onboarding"}
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Radio Browser")
    expect(result.get("data")).to_equal({})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
