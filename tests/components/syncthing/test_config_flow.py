"""Tests for syncthing config flow."""

from unittest.mock import patch

from aiosyncthing.exceptions import UnauthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.syncthing.const import DOMAIN
from homeassistant.const import CONF_NAME, CONF_TOKEN, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

NAME = "Syncthing"
URL = "http://127.0.0.1:8384"
TOKEN = "token"
VERIFY_SSL = True

MOCK_ENTRY = {
    CONF_NAME: NAME,
    CONF_URL: URL,
    CONF_TOKEN: TOKEN,
    CONF_VERIFY_SSL: VERIFY_SSL,
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_setup_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")


@test
async def flow_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test with required fields only."""
    with (
        patch("aiosyncthing.system.System.status", return_value={"myID": "server-id"}),
        patch(
            "homeassistant.components.syncthing.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data={
                CONF_NAME: NAME,
                CONF_URL: URL,
                CONF_TOKEN: TOKEN,
                CONF_VERIFY_SSL: VERIFY_SSL,
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("http://127.0.0.1:8384")
        expect(result["data"][CONF_NAME]).to_equal(NAME)
        expect(result["data"][CONF_URL]).to_equal(URL)
        expect(result["data"][CONF_TOKEN]).to_equal(TOKEN)
        expect(result["data"][CONF_VERIFY_SSL]).to_equal(VERIFY_SSL)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test name is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY, unique_id="server-id")
    entry.add_to_hass(hass)

    with patch("aiosyncthing.system.System.status", return_value={"myID": "server-id"}):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data=MOCK_ENTRY,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid auth."""
    with patch("aiosyncthing.system.System.status", side_effect=UnauthorizedError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data=MOCK_ENTRY,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["token"]).to_equal("invalid_auth")


@test
async def flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cannot connect."""
    with patch("aiosyncthing.system.System.status", side_effect=Exception):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "user"},
            data=MOCK_ENTRY,
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal("cannot_connect")
