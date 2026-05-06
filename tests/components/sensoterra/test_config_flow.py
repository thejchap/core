"""Test the Sensoterra config flow."""

from unittest.mock import AsyncMock

from jwt import DecodeError
from sensoterra.customerapi import InvalidAuth as StInvalidAuth, Timeout as StTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensoterra.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import API_EMAIL, API_PASSWORD, API_TOKEN, HASS_UUID

from tests.common import MockConfigEntry
from tests.components.sensoterra._fixtures import (
    mock_customer_api_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_customer_api_client: AsyncMock = Depends(mock_customer_api_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    hass.data["core.uuid"] = HASS_UUID
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: API_EMAIL,
            CONF_PASSWORD: API_PASSWORD,
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(API_EMAIL)
    expect(result["data"]).to_equal(
        {
            CONF_TOKEN: API_TOKEN,
            CONF_EMAIL: API_EMAIL,
        }
    )

    expect(len(mock_customer_api_client.mock_calls)).to_equal(1)


@test
async def form_unique_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_customer_api_client: AsyncMock = Depends(mock_customer_api_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    hass.data["core.uuid"] = HASS_UUID

    entry = MockConfigEntry(unique_id="39", domain=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: API_EMAIL,
            CONF_PASSWORD: API_PASSWORD,
        },
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    expect(len(mock_customer_api_client.mock_calls)).to_equal(1)


@test.cases(
    test.case("timeout", StTimeout, "cannot_connect"),
    test.case(
        "invalid_auth", StInvalidAuth("Invalid credentials"), "invalid_auth"
    ),
    test.case(
        "decode_error", DecodeError("Bad API token"), "invalid_access_token"
    ),
)
async def form_exceptions(
    exception: type[Exception] | Exception,
    error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_customer_api_client: AsyncMock = Depends(mock_customer_api_client),
) -> None:
    """Test we handle config form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    hass.data["core.uuid"] = HASS_UUID

    mock_customer_api_client.get_token.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: API_EMAIL,
            CONF_PASSWORD: API_PASSWORD,
        },
    )
    expect(result["errors"]).to_equal({"base": error})
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    mock_customer_api_client.get_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: API_EMAIL,
            CONF_PASSWORD: API_PASSWORD,
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(API_EMAIL)
    expect(result["data"]).to_equal(
        {
            CONF_TOKEN: API_TOKEN,
            CONF_EMAIL: API_EMAIL,
        }
    )
    expect(len(mock_customer_api_client.mock_calls)).to_equal(2)
