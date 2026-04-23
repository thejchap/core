"""Test NFAndroidTV config flow."""

from __future__ import annotations

from unittest.mock import patch

from notifications_android_tv.notifications import ConnectError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nfandroidtv.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nfandroidtv import (
    CONF_CONFIG_FLOW,
    CONF_DATA,
    HOST,
    NAME,
    _create_mocked_tv,
    _patch_config_flow_tv,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _patch_setup():
    return patch(
        "homeassistant.components.nfandroidtv.async_setup_entry",
        return_value=True,
    )


@test
async def flow_user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow."""
    mocked_tv = await _create_mocked_tv()
    with _patch_config_flow_tv(mocked_tv), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_CONFIG_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(NAME)
        expect(result["data"]).to_equal(CONF_DATA)


@test
async def flow_user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONF_CONFIG_FLOW,
        unique_id=HOST,
    )
    entry.add_to_hass(hass)

    mocked_tv = await _create_mocked_tv()
    with _patch_config_flow_tv(mocked_tv), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_CONFIG_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unreachable server."""
    mocked_tv = await _create_mocked_tv(True)
    with _patch_config_flow_tv(mocked_tv) as tvmock:
        tvmock.side_effect = ConnectError
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONF_CONFIG_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def flow_user_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unreachable server."""
    mocked_tv = await _create_mocked_tv(True)
    with _patch_config_flow_tv(mocked_tv) as tvmock:
        tvmock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=CONF_CONFIG_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "unknown"})
