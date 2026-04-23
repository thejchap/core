"""Test the nexia config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import aiohttp
from nexia.const import BRAND_ASAIR, BRAND_NEXIA
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nexia.const import CONF_BRAND, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for all tests."""


@test.cases(
    test.case("asair", BRAND_ASAIR),
    test.case("nexia", BRAND_NEXIA),
)
async def form(
    brand: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.nexia.config_flow.NexiaHome.get_name",
            return_value="myhouse",
        ),
        patch(
            "homeassistant.components.nexia.config_flow.NexiaHome.login",
            side_effect=MagicMock(),
        ),
        patch(
            "homeassistant.components.nexia.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_BRAND: brand, CONF_USERNAME: "username", CONF_PASSWORD: "password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("myhouse")
    expect(result2["data"]).to_equal(
        {
            CONF_BRAND: brand,
            CONF_USERNAME: "username",
            CONF_PASSWORD: "password",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("homeassistant.components.nexia.config_flow.NexiaHome.login"),
        patch(
            "homeassistant.components.nexia.config_flow.NexiaHome.get_name",
            return_value=None,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_BRAND: BRAND_NEXIA,
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nexia.config_flow.NexiaHome.login",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_BRAND: BRAND_NEXIA,
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_invalid_auth_http_401(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth error from http 401."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nexia.config_flow.NexiaHome.login",
        side_effect=aiohttp.ClientResponseError(
            status=401, request_info=MagicMock(), history=MagicMock()
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_BRAND: BRAND_NEXIA,
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect_not_found(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect from an http not found error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nexia.config_flow.NexiaHome.login",
        side_effect=aiohttp.ClientResponseError(
            status=404, request_info=MagicMock(), history=MagicMock()
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_BRAND: BRAND_NEXIA,
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_broad_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nexia.config_flow.NexiaHome.login",
        side_effect=ValueError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_BRAND: BRAND_NEXIA,
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
