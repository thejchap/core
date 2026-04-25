"""Tests for Ghost config flow."""

from unittest.mock import AsyncMock

from aioghost.exceptions import GhostAuthError, GhostConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.ghost.const import (
    CONF_ADMIN_API_KEY,
    CONF_API_URL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    API_KEY,
    API_URL,
    SITE_UUID,
    mock_config_entry,
    mock_ghost_api,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

NEW_API_KEY = "new_key_id:new_key_secret"
NEW_API_URL = "https://new.ghost.io"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def form_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _api: AsyncMock = Depends(mock_ghost_api),
) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Ghost")
    expect(result["result"].unique_id).to_equal(SITE_UUID)
    expect(result["data"]).to_equal(
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        }
    )


@test
async def form_invalid_api_key_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test error on invalid API key format."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: "invalid-no-colon",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_api_key"})


@test
async def form_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_ghost_api),
) -> None:
    """Test error when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_auth", side_effect=GhostAuthError("Invalid API key"), error_key="invalid_auth"),
    test.case("cannot_connect", side_effect=GhostConnectionError("Connection failed"), error_key="cannot_connect"),
    test.case("unknown", side_effect=RuntimeError("Unexpected"), error_key="unknown"),
)
async def form_errors_can_recover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(mock_ghost_api),
    *,
    side_effect: Exception,
    error_key: str,
) -> None:
    """Test errors and recovery during setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.get_site.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    api.get_site.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Ghost")
    expect(result["result"].unique_id).to_equal(SITE_UUID)
    expect(result["data"]).to_equal(
        {
            CONF_API_URL: API_URL,
            CONF_ADMIN_API_KEY: API_KEY,
        }
    )


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_ghost_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADMIN_API_KEY: NEW_API_KEY},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_ADMIN_API_KEY]).to_equal(NEW_API_KEY)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", side_effect=GhostAuthError("Invalid API key"), error_key="invalid_auth"),
    test.case("cannot_connect", side_effect=GhostConnectionError("Connection failed"), error_key="cannot_connect"),
    test.case("unknown", side_effect=RuntimeError("Unexpected"), error_key="unknown"),
)
async def reauth_flow_errors_can_recover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_ghost_api),
    *,
    side_effect: Exception,
    error_key: str,
) -> None:
    """Test reauth flow errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    api.get_site.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADMIN_API_KEY: NEW_API_KEY},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    api.get_site.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADMIN_API_KEY: NEW_API_KEY},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_ADMIN_API_KEY]).to_equal(NEW_API_KEY)
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def reauth_flow_invalid_api_key_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with invalid API key format."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADMIN_API_KEY: "invalid-no-colon"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_api_key"})


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_ghost_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: NEW_API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_URL]).to_equal(NEW_API_URL)
    expect(config_entry.data[CONF_ADMIN_API_KEY]).to_equal(NEW_API_KEY)


@test.cases(
    test.case("invalid_auth", side_effect=GhostAuthError("Invalid API key"), error_key="invalid_auth"),
    test.case("cannot_connect", side_effect=GhostConnectionError("Connection failed"), error_key="cannot_connect"),
    test.case("unknown", side_effect=RuntimeError("Unexpected"), error_key="unknown"),
)
async def reconfigure_flow_errors_can_recover(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_ghost_api),
    *,
    side_effect: Exception,
    error_key: str,
) -> None:
    """Test reconfigure flow errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    api.get_site.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: NEW_API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    api.get_site.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: NEW_API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_URL]).to_equal(NEW_API_URL)
    expect(config_entry.data[CONF_ADMIN_API_KEY]).to_equal(NEW_API_KEY)


@test
async def reconfigure_flow_invalid_api_key_format(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_ghost_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow with invalid API key format."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: "invalid-no-colon",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_api_key"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: NEW_API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_URL]).to_equal(NEW_API_URL)
    expect(config_entry.data[CONF_ADMIN_API_KEY]).to_equal(NEW_API_KEY)


@test
async def reconfigure_flow_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_ghost_api),
) -> None:
    """Test reconfigure flow aborts on unique ID mismatch."""
    config_entry.add_to_hass(hass)

    api.get_site.return_value = {
        "title": "Different Ghost",
        "url": NEW_API_URL,
        "site_uuid": "different-uuid",
    }

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_URL: NEW_API_URL,
            CONF_ADMIN_API_KEY: NEW_API_KEY,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
