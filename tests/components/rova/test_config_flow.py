"""Tests for the Rova config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from requests.exceptions import ConnectTimeout, HTTPError
from tryke import Depends, expect, fixture, test

from homeassistant.components.rova.const import (
    CONF_HOUSE_NUMBER,
    CONF_HOUSE_NUMBER_SUFFIX,
    CONF_ZIP_CODE,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_rova

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

ZIP_CODE = "7991AD"
HOUSE_NUMBER = "10"
HOUSE_NUMBER_SUFFIX = "a"


@fixture
def _trigger_executor() -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    hass: HomeAssistant = Depends(hass_fixture),
    rova: MagicMock = Depends(mock_rova),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    data = result.get("data")
    expect(bool(data)).to_be(True)
    expect(data[CONF_ZIP_CODE]).to_equal(ZIP_CODE)
    expect(data[CONF_HOUSE_NUMBER]).to_equal(HOUSE_NUMBER)
    expect(data[CONF_HOUSE_NUMBER_SUFFIX]).to_equal(HOUSE_NUMBER_SUFFIX)


@test
async def error_if_not_rova_area(
    hass: HomeAssistant = Depends(hass_fixture),
    rova: MagicMock = Depends(mock_rova),
) -> None:
    """Test we raise errors if rova does not collect at the given address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    rova.return_value.is_rova_area.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "invalid_rova_area"})

    rova.return_value.is_rova_area.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{ZIP_CODE} {HOUSE_NUMBER} {HOUSE_NUMBER_SUFFIX}")
    expect(result["data"]).to_equal(
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        }
    )


@test
async def abort_if_already_setup(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if rova is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{ZIP_CODE}{HOUSE_NUMBER}{HOUSE_NUMBER_SUFFIX}",
        data={
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("connect_timeout", exception=ConnectTimeout(), error="cannot_connect"),
    test.case("http_error", exception=HTTPError(), error="cannot_connect"),
)
async def abort_if_api_throws_exception(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    rova: MagicMock = Depends(mock_rova),
) -> None:
    """Test different exceptions for the Rova entity."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    rova.return_value.is_rova_area.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    rova.return_value.is_rova_area.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{ZIP_CODE} {HOUSE_NUMBER} {HOUSE_NUMBER_SUFFIX}")
    expect(result["data"]).to_equal(
        {
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        }
    )
