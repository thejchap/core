"""Tests for the Watergate config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from watergate_local_api import WatergateApiException

from homeassistant.components.watergate.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_IP_ADDRESS, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_entry,
    mock_watergate_client,
    mock_webhook_id_generation,
    user_input,
)
from .const import DEFAULT_DEVICE_STATE, DEFAULT_SERIAL_NUMBER, MOCK_WEBHOOK_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def step_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    watergate_client: AsyncMock = Depends(mock_watergate_client),
    _webhook_id: None = Depends(mock_webhook_id_generation),
    inputs: dict[str, str] = Depends(user_input),
) -> None:
    """Test checking if registration form works end to end."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(CONF_IP_ADDRESS in result["data_schema"].schema).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], inputs
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Sonic")
    expect(result["data"]).to_equal({**inputs, CONF_WEBHOOK_ID: MOCK_WEBHOOK_ID})
    expect(result["result"].unique_id).to_equal(DEFAULT_SERIAL_NUMBER)


@test.cases(
    test.case("none_response", client_result=AsyncMock(return_value=None)),
    test.case(
        "api_exception", client_result=AsyncMock(side_effect=WatergateApiException)
    ),
)
async def step_user_form_with_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    watergate_client: AsyncMock = Depends(mock_watergate_client),
    inputs: dict[str, str] = Depends(user_input),
    _webhook_id: None = Depends(mock_webhook_id_generation),
    *,
    client_result: AsyncMock,
) -> None:
    """Test if errors are displayed when an Exception is thrown checking device state."""
    watergate_client.async_get_device_state = client_result

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], inputs
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"][CONF_IP_ADDRESS]).to_equal("cannot_connect")

    watergate_client.async_get_device_state = AsyncMock(
        return_value=DEFAULT_DEVICE_STATE
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], inputs
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Sonic")
    expect(result["data"]).to_equal({**inputs, CONF_WEBHOOK_ID: MOCK_WEBHOOK_ID})


@test
async def abort_if_id_is_not_unique(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    watergate_client: AsyncMock = Depends(mock_watergate_client),
    entry: MockConfigEntry = Depends(mock_entry),
    inputs: dict[str, str] = Depends(user_input),
) -> None:
    """Test checking if we will inform user that this entity is already registered."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(CONF_IP_ADDRESS in result["data_schema"].schema).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], inputs
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
