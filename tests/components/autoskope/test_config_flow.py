"""Test Autoskope config flow."""

from unittest.mock import AsyncMock

from autoskope_client.models import CannotConnect, InvalidAuth
from tryke import Depends, expect, fixture, test

from homeassistant.components.autoskope.const import (
    DEFAULT_HOST,
    DOMAIN,
    SECTION_ADVANCED_SETTINGS,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_autoskope_client, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


USER_INPUT = {
    CONF_USERNAME: "test_user",
    CONF_PASSWORD: "test_password",
    SECTION_ADVANCED_SETTINGS: {
        CONF_HOST: DEFAULT_HOST,
    },
}


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full user config flow from form to entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Autoskope (test_user)")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_HOST: DEFAULT_HOST,
        }
    )
    expect(result["result"].unique_id).to_equal(f"test_user@{DEFAULT_HOST}")


@test.cases(
    test.case(
        "invalid_auth",
        exception=InvalidAuth("Invalid credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=CannotConnect("Connection failed"),
        error="cannot_connect",
    ),
)
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test config flow error handling with recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.__aenter__.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.__aenter__.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_invalid_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow rejects invalid URL with recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            SECTION_ADVANCED_SETTINGS: {
                CONF_HOST: "not-a-valid-url",
            },
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_autoskope_client),
) -> None:
    """Test aborting if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def custom_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow with a custom white-label host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            SECTION_ADVANCED_SETTINGS: {
                CONF_HOST: "https://custom.autoskope.server",
            },
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal("https://custom.autoskope.server")
    expect(result["result"].unique_id).to_equal(
        "test_user@https://custom.autoskope.server"
    )


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth flow updates password and reloads entry."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "new_password",
            CONF_HOST: DEFAULT_HOST,
        }
    )


@test.cases(
    test.case(
        "invalid_auth",
        exception=InvalidAuth("Invalid credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        exception=CannotConnect("Connection failed"),
        error="cannot_connect",
    ),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_autoskope_client),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test reauth flow error handling with recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.__aenter__.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong_password"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.__aenter__.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new_password"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
