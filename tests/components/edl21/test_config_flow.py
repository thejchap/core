"""Test EDL21 config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.edl21.const import CONF_SERIAL_PORT, DEFAULT_TITLE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.edl21._fixtures import mock_setup_entry
from tests.hass_fixtures import hass

VALID_CONFIG = {CONF_SERIAL_PORT: "/dev/ttyUSB1"}
VALID_LEGACY_CONFIG = {CONF_NAME: "My Smart Meter", CONF_SERIAL_PORT: "/dev/ttyUSB1"}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def show_form(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_TITLE)
    expect(result["data"][CONF_SERIAL_PORT]).to_equal(VALID_CONFIG[CONF_SERIAL_PORT])


@test
async def integration_already_exists(
    hass: HomeAssistant = Depends(hass),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that a new entry must not have the same serial port as an existing entry."""
    MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
