"""Test the PrusaLink config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.prusalink.config_flow import InvalidAuth
from homeassistant.components.prusalink.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_version_api as mock_version_api_fx

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_version: dict[str, str] = Depends(mock_version_api_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.prusalink.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "http://1.1.1.1/",
                "username": "abcdefg",
                "password": "abcdefg",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("PrusaXL")
    expect(result2["data"]).to_equal(
        {
            "host": "http://1.1.1.1",
            "username": "abcdefg",
            "password": "abcdefg",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_mk3(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_version_api: dict[str, str] = Depends(mock_version_api_fx),
) -> None:
    """Test it works for MK2/MK3."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_version_api["api"] = "0.9.0-legacy"
    mock_version_api["server"] = "0.7.2"
    mock_version_api["original"] = "PrusaLink I3MK3S"

    with patch(
        "homeassistant.components.prusalink.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "http://1.1.1.1/",
                "username": "abcdefg",
                "password": "abcdefg",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.prusalink.config_flow.PrusaLink.get_version",
        side_effect=InvalidAuth,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "abcdefg",
                "password": "abcdefg",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_unknown(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.prusalink.config_flow.PrusaLink.get_version",
        side_effect=ValueError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "abcdefg",
                "password": "abcdefg",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_too_low_version(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_version_api: dict[str, str] = Depends(mock_version_api_fx),
) -> None:
    """Test we handle too low API version."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_version_api["api"] = "1.2.0"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "1.1.1.1",
            "username": "abcdefg",
            "password": "abcdefg",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "not_supported"})


@test
async def form_invalid_version_2(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_version_api: dict[str, str] = Depends(mock_version_api_fx),
) -> None:
    """Test we handle invalid version."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_version_api["api"] = "i am not a version"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "1.1.1.1",
            "username": "abcdefg",
            "password": "abcdefg",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "not_supported"})


@test
async def form_invalid_mk3_server_version(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_version_api: dict[str, str] = Depends(mock_version_api_fx),
) -> None:
    """Test we handle invalid version for MK2/MK3."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_version_api["api"] = "0.7.2"
    mock_version_api["server"] = "i am not a version"
    mock_version_api["original"] = "PrusaLink I3MK3S"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "host": "1.1.1.1",
            "username": "abcdefg",
            "password": "abcdefg",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "not_supported"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.prusalink.config_flow.PrusaLink.get_version",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "abcdefg",
                "password": "abcdefg",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
