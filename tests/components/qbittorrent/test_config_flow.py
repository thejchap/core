"""Test the qBittorrent config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

import requests_mock
from requests.exceptions import RequestException
from tryke import Depends, expect, fixture, test

from homeassistant.components.qbittorrent.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SOURCE,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_api as mock_api_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USER_INPUT = {
    CONF_URL: "http://localhost:8080",
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pass",
    CONF_VERIFY_SSL: True,
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network + setup_entry mock for every test."""


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_api: requests_mock.Mocker = Depends(mock_api_fx),
) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with requests_mock.Mocker() as mock:
        mock.get(
            f"{USER_INPUT[CONF_URL]}/api/v2/app/preferences",
            exc=RequestException,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    with requests_mock.Mocker() as mock:
        mock.head(USER_INPUT[CONF_URL])
        mock.post(
            f"{USER_INPUT[CONF_URL]}/api/v2/auth/login",
            text="Wrong username/password",
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with requests_mock.Mocker() as mock:
        mock.head(USER_INPUT[CONF_URL])
        mock.post(
            f"{USER_INPUT[CONF_URL]}/api/v2/auth/login",
            text="Ok.",
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_URL: "http://localhost:8080",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
            CONF_VERIFY_SSL: True,
        }
    )


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(domain=DOMAIN, data=USER_INPUT)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
