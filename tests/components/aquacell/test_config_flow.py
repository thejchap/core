"""Test the Aquacell config flow."""

from unittest.mock import AsyncMock

from aioaquacell import ApiException, AuthenticationFailed
from tryke import Depends, expect, fixture, test

from homeassistant.components.aquacell.const import (
    CONF_BRAND,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import TEST_CONFIG_ENTRY, TEST_USER_INPUT
from ._fixtures import mock_aquacell_api, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **TEST_CONFIG_ENTRY,
        },
        unique_id=TEST_CONFIG_ENTRY[CONF_EMAIL],
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _api: AsyncMock = Depends(mock_aquacell_api),
) -> None:
    """Test the full config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result2["data"][CONF_EMAIL]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result2["data"][CONF_PASSWORD]).to_equal(TEST_CONFIG_ENTRY[CONF_PASSWORD])
    expect(result2["data"][CONF_REFRESH_TOKEN]).to_equal(TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN])
    expect(result2["data"][CONF_BRAND]).to_equal(TEST_CONFIG_ENTRY[CONF_BRAND])
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("api_exception", exception=ApiException, error="cannot_connect"),
    test.case("timeout", exception=TimeoutError, error="cannot_connect"),
    test.case("auth_failed", exception=AuthenticationFailed, error="invalid_auth"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def form_exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    aquacell_api: AsyncMock = Depends(mock_aquacell_api),
) -> None:
    """Test we handle form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    aquacell_api.authenticate.side_effect = exception
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})

    aquacell_api.authenticate.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result3["data"][CONF_EMAIL]).to_equal(TEST_CONFIG_ENTRY[CONF_EMAIL])
    expect(result3["data"][CONF_PASSWORD]).to_equal(TEST_CONFIG_ENTRY[CONF_PASSWORD])
    expect(result3["data"][CONF_REFRESH_TOKEN]).to_equal(TEST_CONFIG_ENTRY[CONF_REFRESH_TOKEN])
    expect(result3["data"][CONF_BRAND]).to_equal(TEST_CONFIG_ENTRY[CONF_BRAND])
    expect(len(setup_entry.mock_calls)).to_equal(1)
