"""Test Discord config flow."""

from unittest.mock import MagicMock

import nextcord
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.discord.const import DOMAIN
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.discord import (
    CONF_DATA,
    CONF_INPUT,
    NAME,
    create_entry,
    mock_exception,
    mocked_discord_info,
    patch_discord_login,
)
from tests.components.discord._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with duplicate server."""
    create_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with invalid token."""
    with patch_discord_login() as mock:
        mock.side_effect = nextcord.LoginFailure
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_discord_login() as mock:
        mock.side_effect = mock_exception()
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_unknown_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_discord_login() as mock:
        mock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONF_DATA,
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})

    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_INPUT,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(NAME)
    expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test a reauth flow."""
    entry = create_entry(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")

    new_conf = {CONF_API_TOKEN: "1234567890123"}
    with patch_discord_login() as mock:
        mock.side_effect = nextcord.LoginFailure
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with mocked_discord_info(), patch_discord_login():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data).to_equal(CONF_DATA | new_conf)
