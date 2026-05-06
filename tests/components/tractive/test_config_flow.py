"""Test the tractive config flow."""

from http import HTTPStatus
from unittest.mock import patch

import aiohttp
import aiotractive
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tractive.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USER_INPUT = {
    "email": "test-email@example.com",
    "password": "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch("aiotractive.api.API.user_id", return_value="user_id"),
        patch(
            "homeassistant.components.tractive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("test-email@example.com")
    expect(result2["data"]).to_equal(USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=aiotractive.exceptions.UnauthorizedError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=aiotractive.exceptions.TractiveError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_rate_limit_exceeded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle rate limit error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    cause = aiohttp.ClientResponseError(
        None,
        (),
        status=HTTPStatus.TOO_MANY_REQUESTS,
    )
    error = aiotractive.exceptions.TractiveError()
    error.__cause__ = cause

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=error,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "rate_limit_exceeded"})


@test
async def form_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    first_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    first_entry.add_to_hass(hass)

    with patch("aiotractive.api.API.user_id", return_value="USERID"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch("aiotractive.api.API.user_id", return_value="USERID"),
        patch(
            "homeassistant.components.tractive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauthentication_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication failure."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=aiotractive.exceptions.UnauthorizedError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("invalid_auth")


@test
async def reauthentication_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication with connection error."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=aiotractive.exceptions.TractiveError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("cannot_connect")


@test
async def reauthentication_rate_limit_exceeded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication with rate limit error."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    cause = aiohttp.ClientResponseError(
        None,
        (),
        status=HTTPStatus.TOO_MANY_REQUESTS,
    )
    error = aiotractive.exceptions.TractiveError()
    error.__cause__ = cause

    with patch("aiotractive.api.API.user_id", side_effect=error):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("rate_limit_exceeded")


@test
async def reauthentication_unknown_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication failure."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "aiotractive.api.API.user_id",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["step_id"]).to_equal("reauth_confirm")
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]["base"]).to_equal("unknown")


@test
async def reauthentication_failure_no_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Tractive reauthentication with no existing entry."""
    old_entry = MockConfigEntry(
        domain="tractive",
        data=USER_INPUT,
        unique_id="USERID",
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch("aiotractive.api.API.user_id", return_value="USERID_DIFFERENT"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_failed_existing")
