"""Define tests for the Acmeda config flow."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import aiopulse
from tryke import Depends, expect, fixture, test

from homeassistant.components.acmeda.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_hub_discover, mock_hub_run

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DUMMY_HOST1 = "127.0.0.1"
DUMMY_HOST2 = "127.0.0.2"

CONFIG = {
    CONF_HOST: DUMMY_HOST1,
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _async_generator(items: list[object]) -> AsyncIterator[object]:
    """Async yields items provided in a list."""
    for item in items:
        yield item


@test
async def show_form_no_hubs(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
) -> None:
    """Test that flow aborts if no hubs are discovered."""
    discover.return_value = _async_generator([])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
    expect(len(discover.mock_calls)).to_equal(1)


@test
async def timeout_fetching_hub(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
) -> None:
    """Test that flow aborts on timeout."""
    discover.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
    expect(len(discover.mock_calls)).to_equal(1)


@test
async def show_form_one_hub(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
    _run: AsyncMock = Depends(mock_hub_run),
) -> None:
    """Test that a config is created when one hub discovered."""
    dummy_hub_1 = aiopulse.Hub(DUMMY_HOST1)
    dummy_hub_1.id = "ABC123"

    discover.return_value = _async_generator([dummy_hub_1])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(dummy_hub_1.id)
    expect(result["result"].data).to_equal({CONF_HOST: DUMMY_HOST1})

    expect(len(discover.mock_calls)).to_equal(1)


@test
async def show_form_two_hubs(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
) -> None:
    """Test that the form is served when more than one hub discovered."""
    dummy_hub_1 = aiopulse.Hub(DUMMY_HOST1)
    dummy_hub_1.id = "ABC123"

    dummy_hub_2 = aiopulse.Hub(DUMMY_HOST1)
    dummy_hub_2.id = "DEF456"

    discover.return_value = _async_generator([dummy_hub_1, dummy_hub_2])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(len(discover.mock_calls)).to_equal(1)


@test
async def create_second_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
    _run: AsyncMock = Depends(mock_hub_run),
) -> None:
    """Test that a config is created when a second hub is discovered."""
    dummy_hub_1 = aiopulse.Hub(DUMMY_HOST1)
    dummy_hub_1.id = "ABC123"

    dummy_hub_2 = aiopulse.Hub(DUMMY_HOST2)
    dummy_hub_2.id = "DEF456"

    discover.return_value = _async_generator([dummy_hub_1, dummy_hub_2])

    MockConfigEntry(domain=DOMAIN, unique_id=dummy_hub_1.id, data=CONFIG).add_to_hass(
        hass
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(dummy_hub_2.id)
    expect(result["result"].data).to_equal({CONF_HOST: DUMMY_HOST2})


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discover: MagicMock = Depends(mock_hub_discover),
) -> None:
    """Test that flow aborts when all hubs are configured."""
    dummy_hub_1 = aiopulse.Hub(DUMMY_HOST1)
    dummy_hub_1.id = "ABC123"

    discover.return_value = _async_generator([dummy_hub_1])

    MockConfigEntry(domain=DOMAIN, unique_id=dummy_hub_1.id, data=CONFIG).add_to_hass(
        hass
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
