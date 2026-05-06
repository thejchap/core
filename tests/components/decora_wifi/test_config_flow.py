"""Tests for the Leviton Decora Wi-Fi config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.decora_wifi.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_decora_wifi, mock_setup_entry
from .const import TEST_USER_ID, TEST_USERNAME, USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _decora: MagicMock = Depends(mock_decora_wifi),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a successful user-initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_USER_ID)


@test.cases(
    test.case(
        "invalid_auth",
        login_return_value=None,
        login_side_effect=None,
        expected_error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        login_return_value=True,
        login_side_effect=ValueError("Cannot connect"),
        expected_error="cannot_connect",
    ),
)
async def user_flow_error_and_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    decora: MagicMock = Depends(mock_decora_wifi),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    login_return_value: bool | None,
    login_side_effect: Exception | None,
    expected_error: str,
) -> None:
    """Test user flow shows the correct error and that the user can retry successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # First attempt: error
    decora.login.return_value = login_return_value
    decora.login.side_effect = login_side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    # Second attempt: success
    decora.login.side_effect = None
    decora.login.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _decora: MagicMock = Depends(mock_decora_wifi),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate accounts are rejected."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def import_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _decora: MagicMock = Depends(mock_decora_wifi),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a successful YAML import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_USER_ID)


@test
async def import_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    decora: MagicMock = Depends(mock_decora_wifi),
) -> None:
    """Test YAML import aborts on invalid auth."""
    decora.login.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_auth")


@test
async def import_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    decora: MagicMock = Depends(mock_decora_wifi),
) -> None:
    """Test YAML import aborts when connection fails."""
    decora.login.side_effect = ValueError("Cannot connect")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def import_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _decora: MagicMock = Depends(mock_decora_wifi),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test YAML import aborts when username already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data=USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
