"""Tests for the TotalConnect config flow."""

from unittest.mock import AsyncMock, patch

from total_connect_client.exceptions import AuthenticationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.totalconnect.const import (
    AUTO_BYPASS,
    CODE_REQUIRED,
    CONF_USERCODES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LOCATION, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import (
    mock_client,
    mock_config_entry,
    mock_location,
    mock_setup_entry,
)
from .const import LOCATION_ID, PASSWORD, USERNAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("locations")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_PASSWORD: PASSWORD,
            CONF_USERNAME: USERNAME,
            CONF_USERCODES: {LOCATION_ID: "7890"},
        }
    )
    expect(result["title"]).to_equal("Total Connect")
    expect(result["options"]).to_equal({})
    expect(result["result"].unique_id).to_equal(USERNAME)


@test
async def login_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Test login errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.totalconnect.config_flow.TotalConnectClient",
    ) as client:
        client.side_effect = AuthenticationError()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("locations")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def usercode_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
    location: AsyncMock = Depends(mock_location),
) -> None:
    """Test user step with usercode errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("locations")

    location.set_usercode.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("locations")
    expect(result["errors"]).to_equal({CONF_LOCATION: "usercode"})

    location.set_usercode.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERCODES: "7890"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def no_locations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_client),
    _location: AsyncMock = Depends(mock_location),
) -> None:
    """Test no locations found."""
    client.get_number_locations.return_value = 0
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_locations")


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort if the account is already setup."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test login errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "abc"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data[CONF_PASSWORD]).to_equal("abc")


@test
async def reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test login errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.totalconnect.config_flow.TotalConnectClient",
    ) as client:
        client.side_effect = AuthenticationError()

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: PASSWORD}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow options."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={AUTO_BYPASS: True, CODE_REQUIRED: False}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({AUTO_BYPASS: True, CODE_REQUIRED: False})
