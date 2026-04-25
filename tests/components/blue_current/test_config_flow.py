"""Test the Blue Current config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.blue_current import DOMAIN
from homeassistant.components.blue_current.config_flow import (
    AlreadyConnected,
    InvalidApiToken,
    RequestLimitReached,
    WebsocketError,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import config_entry as config_entry_fx

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the form is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["errors"]).to_equal({})
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the api token is set."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["errors"]).to_equal({})
    expect(result["type"]).to_be(FlowResultType.FORM)

    with (
        patch(
            "homeassistant.components.blue_current.config_flow.Client.validate_api_token",
            return_value="1234",
        ),
        patch(
            "homeassistant.components.blue_current.config_flow.Client.get_email",
            return_value="test@email.com",
        ),
        patch(
            "homeassistant.components.blue_current.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_token": "123",
            },
        )
        await hass.async_block_till_done()

    expect(result2["title"]).to_equal("test@email.com")
    expect(result2["data"]).to_equal({"api_token": "123"})
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("invalid_token", error=InvalidApiToken(), message="invalid_token"),
    test.case("limit_reached", error=RequestLimitReached(), message="limit_reached"),
    test.case("already_connected", error=AlreadyConnected(), message="already_connected"),
    test.case("unknown", error=Exception(), message="unknown"),
    test.case("websocket_error", error=WebsocketError(), message="cannot_connect"),
)
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    error: Exception,
    message: str,
) -> None:
    """Test bluecurrent api errors during configuration flow."""
    with patch(
        "homeassistant.components.blue_current.config_flow.Client.validate_api_token",
        side_effect=error,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        expect(result["errors"]["base"]).to_equal(message)
        expect(result["type"]).to_be(FlowResultType.FORM)

    with (
        patch(
            "homeassistant.components.blue_current.config_flow.Client.validate_api_token",
            return_value="1234",
        ),
        patch(
            "homeassistant.components.blue_current.config_flow.Client.get_email",
            return_value="test@email.com",
        ),
        patch(
            "homeassistant.components.blue_current.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_token": "123",
            },
        )
        await hass.async_block_till_done()

        expect(result2["title"]).to_equal("test@email.com")
        expect(result2["data"]).to_equal({"api_token": "123"})
        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case(
        "reauth_successful",
        customer_id="1234",
        reason="reauth_successful",
        expected_api_token="1234567890",
    ),
    test.case(
        "wrong_account",
        customer_id="6666",
        reason="wrong_account",
        expected_api_token="123",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    *,
    customer_id: str,
    reason: str,
    expected_api_token: str,
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.blue_current.config_flow.Client.validate_api_token",
            return_value=customer_id,
        ),
        patch(
            "homeassistant.components.blue_current.config_flow.Client.get_email",
            return_value="test@email.com",
        ),
        patch(
            "homeassistant.components.blue_current.config_flow.Client.wait_for_charge_points",
        ),
        patch(
            "homeassistant.components.blue_current.Client.connect",
            lambda self, on_data, on_open: hass.loop.create_future(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_token": "1234567890"},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal(reason)
        expect(config_entry.data["api_token"]).to_equal(expected_api_token)

        await hass.async_block_till_done()
