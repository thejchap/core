"""Test the Wolf SmartSet Service config flow."""

from unittest.mock import patch

from httpcore import ConnectError
from tryke import Depends, expect, fixture, test
from wolf_comm.models import Device
from wolf_comm.token_auth import InvalidAuth

from homeassistant import config_entries
from homeassistant.components.wolflink.const import (
    DEVICE_GATEWAY,
    DEVICE_ID,
    DEVICE_NAME,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

INPUT_CONFIG = {
    CONF_USERNAME: CONFIG[CONF_USERNAME],
    CONF_PASSWORD: CONFIG[CONF_PASSWORD],
}

DEVICE = Device(CONFIG[DEVICE_ID], CONFIG[DEVICE_GATEWAY], CONFIG[DEVICE_NAME])


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def device_step_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the second step of config."""
    with patch(
        "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
        return_value=[DEVICE],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("device")


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entity creation from device step."""
    with (
        patch(
            "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
            return_value=[DEVICE],
        ),
        patch(
            "homeassistant.components.wolflink.async_setup_entry", return_value=True
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

        result_create_entry = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device_name": CONFIG[DEVICE_NAME]},
        )

    expect(result_create_entry["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result_create_entry["title"]).to_equal(CONFIG[DEVICE_NAME])
    expect(result_create_entry["data"]).to_equal(CONFIG)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    with patch(
        "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
        side_effect=ConnectError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    with patch(
        "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def already_configured_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test already configured while creating entry."""
    with (
        patch(
            "homeassistant.components.wolflink.config_flow.WolfClient.fetch_system_list",
            return_value=[DEVICE],
        ),
        patch(
            "homeassistant.components.wolflink.async_setup_entry", return_value=True
        ),
    ):
        MockConfigEntry(
            domain=DOMAIN, unique_id=str(CONFIG[DEVICE_ID]), data=CONFIG
        ).add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=INPUT_CONFIG,
        )

        result_create_entry = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device_name": CONFIG[DEVICE_NAME]},
        )

    expect(result_create_entry["type"]).to_be(FlowResultType.ABORT)
    expect(result_create_entry["reason"]).to_equal("already_configured")
