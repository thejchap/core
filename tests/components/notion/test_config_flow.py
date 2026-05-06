"""Define tests for the Notion config flow."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aionotion.errors import InvalidCredentialsError, NotionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.notion.const import (
    CONF_REFRESH_TOKEN,
    CONF_USER_UUID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_USER_UUID,
    TEST_USERNAME,
    client,
    config,
    config_entry,
    data_bridge,
    data_listener,
    data_sensor,
    data_user_preferences,
    mock_aionotion,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _network: None = Depends(mock_network),
) -> None:
    """Module-level fixture priming common mocks."""


@test.cases(
    test.case(
        "unknown",
        get_client_with_exception=AsyncMock(side_effect=Exception),
        errors={"base": "unknown"},
    ),
    test.case(
        "invalid_auth",
        get_client_with_exception=AsyncMock(side_effect=InvalidCredentialsError),
        errors={"base": "invalid_auth"},
    ),
    test.case(
        "notion_error",
        get_client_with_exception=AsyncMock(side_effect=NotionError),
        errors={"base": "unknown"},
    ),
)
async def create_entry(
    get_client_with_exception: AsyncMock,
    errors: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: Mock = Depends(client),
    _aionotion: None = Depends(mock_aionotion),
) -> None:
    """Test creating an etry (including recovery from errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.notion.config_flow.async_get_client_with_credentials",
        get_client_with_exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_REFRESH_TOKEN: TEST_REFRESH_TOKEN,
            CONF_USERNAME: TEST_USERNAME,
            CONF_USER_UUID: TEST_USER_UUID,
        }
    )


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config),
    _entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=cfg
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "unknown",
        get_client_with_exception=AsyncMock(side_effect=Exception),
        errors={"base": "unknown"},
    ),
    test.case(
        "invalid_auth",
        get_client_with_exception=AsyncMock(side_effect=InvalidCredentialsError),
        errors={"base": "invalid_auth"},
    ),
    test.case(
        "notion_error",
        get_client_with_exception=AsyncMock(side_effect=NotionError),
        errors={"base": "unknown"},
    ),
)
async def reauth(
    get_client_with_exception: AsyncMock,
    errors: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _cfg: dict[str, Any] = Depends(config),
    entry: MockConfigEntry = Depends(config_entry),
    _aionotion: None = Depends(mock_aionotion),
) -> None:
    """Test that re-auth works."""
    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.notion.config_flow.async_get_client_with_credentials",
        get_client_with_exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PASSWORD: "password"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "password"}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
