"""Test the IoTawatt config flow."""

from unittest.mock import patch

import httpx
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.iotawatt.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    with (
        patch(
            "homeassistant.components.iotawatt.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(
        {
            "host": "1.1.1.1",
        }
    )


@test
async def form_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("auth")

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        return_value=False,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "mock-user",
                "password": "mock-pass",
            },
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["step_id"]).to_equal("auth")
    expect(result3["errors"]).to_equal({"base": "invalid_auth"})

    with (
        patch(
            "homeassistant.components.iotawatt.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
            return_value=True,
        ),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "mock-user",
                "password": "mock-pass",
            },
        )
        await hass.async_block_till_done()

    expect(result4["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result4["data"]).to_equal(
        {
            "host": "1.1.1.1",
            "username": "mock-user",
            "password": "mock-pass",
        }
    )


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        side_effect=httpx.HTTPError("any"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_setup_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle broad exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
