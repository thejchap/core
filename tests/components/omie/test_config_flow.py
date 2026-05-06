"""Test the OMIE - Spain and Portugal electricity prices config flow."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.omie.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import spot_price_fetcher
from ._fixtures import mock_config_entry, mock_pyomie, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _pyomie: MagicMock = Depends(mock_pyomie),
    _network: None = Depends(mock_network),
) -> None:
    """Module-level fixture priming common mocks."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("OMIE")
    expect(result2["data"]).to_equal({})
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyomie: MagicMock = Depends(mock_pyomie),
) -> None:
    """Test we handle connection error."""
    pyomie.spot_price.side_effect = aiohttp.ClientError("Connection failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    pyomie.spot_price.side_effect = spot_price_fetcher({})
    result3 = await hass.config_entries.flow.async_configure(result2["flow_id"], {})
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already set up."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    expect(len(setup_entry.mock_calls)).to_equal(0)
