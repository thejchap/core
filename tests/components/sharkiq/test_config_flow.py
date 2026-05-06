"""Test the Shark IQ config flow."""

from unittest.mock import patch

import aiohttp
from sharkiq import AylaApi, SharkIqAuthError, SharkIqError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.sharkiq.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from .const import (
    CONFIG,
    CONFIG_NO_REGION,
    TEST_PASSWORD,
    TEST_REGION,
    TEST_USERNAME,
    UNIQUE_ID,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_success_no_region(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data=CONFIG_NO_REGION
    )
    mock_config.add_to_hass(hass)

    with patch("homeassistant.components.sharkiq.async_setup_entry", return_value=True):
        result = await async_setup_component(hass=hass, domain=DOMAIN, config={})

    expect(result).to_be(True)


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
    expect(result["errors"]).to_equal({})

    with (
        patch("sharkiq.AylaApi.async_sign_in", return_value=True),
        patch("sharkiq.AylaApi.async_set_cookie"),
        patch(
            "homeassistant.components.sharkiq.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(f"{TEST_USERNAME:s}")
    expect(result2["data"]).to_equal(
        {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "region": TEST_REGION,
        }
    )

    await hass.async_block_till_done()
    mock_setup_entry.assert_called_once()


@test.cases(
    test.case("invalid_auth", exc=SharkIqAuthError, base_error="invalid_auth"),
    test.case("client_error", exc=aiohttp.ClientError, base_error="cannot_connect"),
    test.case("type_error", exc=TypeError, base_error="cannot_connect"),
    test.case("shark_error", exc=SharkIqError, base_error="unknown"),
)
async def form_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exc: type[Exception],
    base_error: str,
) -> None:
    """Test form errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch.object(AylaApi, "async_sign_in", side_effect=exc),
        patch("sharkiq.AylaApi.async_set_cookie"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"].get("base")).to_equal(base_error)


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data=CONFIG)
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    with (
        patch("sharkiq.AylaApi.async_sign_in", return_value=True),
        patch("sharkiq.AylaApi.async_set_cookie"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test.cases(
    test.case(
        "auth_form",
        side_effect=SharkIqAuthError,
        result_type="form",
        msg_field="errors",
        msg="invalid_auth",
    ),
    test.case(
        "client_abort",
        side_effect=aiohttp.ClientError,
        result_type="abort",
        msg_field="reason",
        msg="cannot_connect",
    ),
    test.case(
        "type_abort",
        side_effect=TypeError,
        result_type="abort",
        msg_field="reason",
        msg="cannot_connect",
    ),
    test.case(
        "unknown_abort",
        side_effect=SharkIqError,
        result_type="abort",
        msg_field="reason",
        msg="unknown",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    result_type: str,
    msg_field: str,
    msg: str,
) -> None:
    """Test reauth failures."""
    mock_config = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data=CONFIG)
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)

    with (
        patch("sharkiq.AylaApi.async_sign_in", side_effect=side_effect),
        patch("sharkiq.AylaApi.async_set_cookie"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=CONFIG
        )
        msg_value = result[msg_field]
        if msg_field == "errors":
            msg_value = msg_value.get("base")

        expect(result["type"]).to_equal(result_type)
        expect(msg_value).to_equal(msg)
