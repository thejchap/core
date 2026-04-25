"""Test the wiffi integration config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.wiffi.const import DOMAIN
from homeassistant.const import CONF_PORT, CONF_TIMEOUT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import addr_in_use, dummy_tcp_server, mock_setup_entry, start_server_failed

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_CONFIG = {CONF_PORT: 8765}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _server: object = Depends(dummy_tcp_server),
) -> None:
    """Test how we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_addr_in_use(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _server: object = Depends(addr_in_use),
) -> None:
    """Test how we handle addr_in_use error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("addr_in_use")


@test
async def form_start_server_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _server: object = Depends(start_server_failed),
) -> None:
    """Test how we handle start_server_failed error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("start_server_failed")


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test option flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    expect(bool(entry.options)).to_be(False)

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_TIMEOUT: 9}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("")
    expect(result["data"][CONF_TIMEOUT]).to_equal(9)
