"""Test pushbullet config flow."""

from __future__ import annotations

from unittest.mock import patch

from pushbullet import InvalidKeyError, PushbulletError
from requests_mock import Mocker
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.pushbullet.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_CONFIG
from ._fixtures import (
    mock_setup_entry as mock_setup_entry_fx,
    requests_mock_fixture as requests_mock_fixture_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network + pushbullet setup mock for every test."""


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _requests: Mocker = Depends(requests_mock_fixture_fx),
) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("pushbullet")
    expect(result["data"]).to_equal(MOCK_CONFIG)


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _requests: Mocker = Depends(requests_mock_fixture_fx),
) -> None:
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="ujpah72o0",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_name_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="MYAPIKEY",
    )
    entry.add_to_hass(hass)

    new_config = MOCK_CONFIG.copy()
    new_config[CONF_API_KEY] = "NEWKEY"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=new_config,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_invalid_key(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with invalid api key."""
    with patch(
        "homeassistant.components.pushbullet.config_flow.PushBullet",
        side_effect=InvalidKeyError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})


@test
async def flow_conn_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow with conn error."""
    with patch(
        "homeassistant.components.pushbullet.config_flow.PushBullet",
        side_effect=PushbulletError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_CONFIG,
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
