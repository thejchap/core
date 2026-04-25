"""Test the V2C config flow."""

from unittest.mock import AsyncMock

from pytrydan.exceptions import TrydanError
from tryke import Depends, expect, fixture, test

from homeassistant.components.v2c.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_v2c_client

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _v2c_client: AsyncMock = Depends(mock_v2c_client),
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EVSE 1.1.1.1")
    expect(result["data"]).to_equal({CONF_HOST: "1.1.1.1"})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("cannot_connect", side_effect=TrydanError, error="cannot_connect"),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    v2c_client: AsyncMock = Depends(mock_v2c_client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    v2c_client.get_data.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})
    v2c_client.get_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("EVSE 1.1.1.1")
    expect(result["data"]).to_equal({CONF_HOST: "1.1.1.1"})
