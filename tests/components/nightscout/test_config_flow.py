"""Test the Nightscout config flow."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import patch

from aiohttp import ClientConnectionError, ClientResponseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nightscout.const import DOMAIN
from homeassistant.components.nightscout.utils import hash_from_url
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nightscout import (
    GLUCOSE_READINGS,
    SERVER_STATUS,
    SERVER_STATUS_STATUS_ONLY,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {CONF_URL: "https://some.url:1234"}


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _patch_async_setup_entry():
    return patch(
        "homeassistant.components.nightscout.async_setup_entry",
        return_value=True,
    )


def _patch_glucose_readings():
    return patch(
        "homeassistant.components.nightscout.NightscoutAPI.get_sgvs",
        return_value=GLUCOSE_READINGS,
    )


def _patch_server_status():
    return patch(
        "homeassistant.components.nightscout.NightscoutAPI.get_server_status",
        return_value=SERVER_STATUS,
    )


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the user initiated form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        _patch_glucose_readings(),
        _patch_server_status(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal(SERVER_STATUS.name)
        expect(result2["data"]).to_equal(CONFIG)
        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=ClientConnectionError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_form_api_key_required(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle an unauthorized error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.nightscout.NightscoutAPI.get_server_status",
            return_value=SERVER_STATUS_STATUS_ONLY,
        ),
        patch(
            "homeassistant.components.nightscout.NightscoutAPI.get_sgvs",
            side_effect=ClientResponseError(
                None, None, status=HTTPStatus.UNAUTHORIZED
            ),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_form_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nightscout.NightscoutAPI.get_server_status",
        side_effect=Exception(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_URL: "https://some.url:1234"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def user_form_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test duplicate entries."""
    with _patch_glucose_readings(), _patch_server_status():
        unique_id = hash_from_url(CONFIG[CONF_URL])
        entry = MockConfigEntry(domain=DOMAIN, unique_id=unique_id)
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONFIG,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")
