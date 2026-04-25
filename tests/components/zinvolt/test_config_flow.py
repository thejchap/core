"""Test the Zinvolt config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from zinvolt.exceptions import ZinvoltAuthenticationError, ZinvoltError

from homeassistant.components.zinvolt.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_zinvolt_client
from .const import TOKEN

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_zinvolt_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@test.com",
            CONF_PASSWORD: "yes",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@test.com")
    expect(result["data"]).to_equal({CONF_ACCESS_TOKEN: TOKEN})
    expect(result["result"].unique_id).to_equal("a0226b8f-98fe-4524-b369-272b466b8797")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        exception=ZinvoltAuthenticationError,
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=ZinvoltError,
        error="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=Exception,
        error="unknown",
    ),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_zinvolt_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@test.com",
            CONF_PASSWORD: "yes",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@test.com",
            CONF_PASSWORD: "yes",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_zinvolt_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle duplicate entries."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@test.com",
            CONF_PASSWORD: "yes",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
