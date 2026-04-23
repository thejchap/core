"""The tests for the litejet component."""

from unittest.mock import Mock, patch

from serial import SerialException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.litejet.const import CONF_DEFAULT_TRANSITION, DOMAIN
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_litejet

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def show_config_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_litejet: Mock = Depends(mock_litejet),
) -> None:
    """Test create entry from user input."""
    test_data = {CONF_PORT: "/dev/test"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("/dev/test")
    expect(result["data"]).to_equal(test_data)


@test
async def flow_entry_already_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user input when a config entry already exists."""
    first_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PORT: "/dev/first"},
    )
    first_entry.add_to_hass(hass)

    test_data = {CONF_PORT: "/dev/test"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def flow_open_failed(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user input when serial port open fails."""
    test_data = {CONF_PORT: "/dev/test"}

    with patch("pylitejet.LiteJet") as mock_pylitejet:
        mock_pylitejet.side_effect = SerialException

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"][CONF_PORT]).to_equal("open_failed")


@test
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test updating options."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_PORT: "/dev/test"})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_DEFAULT_TRANSITION: 12},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_DEFAULT_TRANSITION: 12})
