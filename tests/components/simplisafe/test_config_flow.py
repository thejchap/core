"""Define tests for the SimpliSafe config flow."""

from unittest.mock import patch

from simplipy.errors import InvalidCredentialsError, SimplipyError
from tryke import Depends, expect, fixture, test

from homeassistant.components.simplisafe import DOMAIN
from homeassistant.components.simplisafe.config_flow import CONF_AUTH_CODE
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_CODE, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    config_entry,
    config_entry_other_id,
    setup_simplisafe,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_AUTH_CODE = "code12345123451234512345123451234512345123451"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(config_entry),
    _setup: None = Depends(setup_simplisafe),
) -> None:
    """Test that errors are shown when duplicates are added."""
    with patch(
        "homeassistant.components.simplisafe.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["step_id"]).to_equal("user")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_AUTH_CODE: VALID_AUTH_CODE}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def invalid_auth_code_length(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that an invalid auth code length show the correct error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_AUTH_CODE: "too_short_code"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_AUTH_CODE: "invalid_auth_code_length"})


@test
async def invalid_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that invalid credentials show the correct error."""
    with patch(
        "homeassistant.components.simplisafe.config_flow.API.async_from_auth",
        side_effect=InvalidCredentialsError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["step_id"]).to_equal("user")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_AUTH_CODE: VALID_AUTH_CODE},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_AUTH_CODE: "invalid_auth"})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test config flow options."""
    with patch(
        "homeassistant.components.simplisafe.async_setup_entry", return_value=True
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_CODE: "4321"}
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(entry.options).to_equal({CONF_CODE: "4321"})


@test
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _setup: None = Depends(setup_simplisafe),
) -> None:
    """Test the re-auth step."""
    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.simplisafe.async_setup_entry", return_value=True
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_AUTH_CODE: VALID_AUTH_CODE}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    [final_entry] = hass.config_entries.async_entries(DOMAIN)
    expect(final_entry.data).to_equal({CONF_USERNAME: "12345", CONF_TOKEN: "token123"})


@test
async def step_reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry_other_id),
    _setup: None = Depends(setup_simplisafe),
) -> None:
    """Test the re-auth step where the wrong account is used during login."""
    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.simplisafe.async_setup_entry", return_value=True
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_AUTH_CODE: VALID_AUTH_CODE}
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("wrong_account")


@test.cases(
    test.case("plain_code", auth_code=VALID_AUTH_CODE),
    test.case("equals_prefix", auth_code=f"={VALID_AUTH_CODE}"),
)
async def step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_simplisafe),
    *,
    auth_code: str,
) -> None:
    """Test successfully completion of the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "homeassistant.components.simplisafe.async_setup_entry", return_value=True
        ),
        patch("homeassistant.config_entries.ConfigEntries.async_reload"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_AUTH_CODE: auth_code}
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(len(hass.config_entries.async_entries())).to_equal(1)
    [final_entry] = hass.config_entries.async_entries(DOMAIN)
    expect(final_entry.data).to_equal({CONF_USERNAME: "12345", CONF_TOKEN: "token123"})


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_simplisafe),
) -> None:
    """Test that an unknown error shows ohe correct error."""
    with patch(
        "homeassistant.components.simplisafe.config_flow.API.async_from_auth",
        side_effect=SimplipyError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        expect(result["step_id"]).to_equal("user")
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_AUTH_CODE: VALID_AUTH_CODE}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "unknown"})
