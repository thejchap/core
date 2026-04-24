"""Test the QNAP config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from requests.exceptions import ConnectTimeout
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.qnap import const
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_HOST,
    TEST_PASSWORD,
    TEST_SERIAL,
    TEST_USERNAME,
    mock_setup_entry as mock_setup_entry_fx,
    qnap_connect as qnap_connect_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

STANDARD_CONFIG = {
    CONF_USERNAME: TEST_USERNAME,
    CONF_PASSWORD: TEST_PASSWORD,
    CONF_HOST: TEST_HOST,
}

ENTRY_DATA = {
    CONF_HOST: TEST_HOST,
    CONF_USERNAME: TEST_USERNAME,
    CONF_PASSWORD: TEST_PASSWORD,
    CONF_SSL: const.DEFAULT_SSL,
    CONF_VERIFY_SSL: const.DEFAULT_VERIFY_SSL,
    CONF_PORT: const.DEFAULT_PORT,
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _qnap: MagicMock = Depends(qnap_connect_fx),
) -> None:
    """Wire mock_network + mock_setup_entry + qnap_connect for every test."""


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    qnap_connect: MagicMock = Depends(qnap_connect_fx),
) -> None:
    """Config flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    qnap_connect.get_system_stats.side_effect = ConnectTimeout("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    qnap_connect.get_system_stats.side_effect = TypeError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    qnap_connect.get_system_stats.side_effect = Exception("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unknown"})

    qnap_connect.get_system_stats.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test NAS name")
    expect(result["data"]).to_equal(ENTRY_DATA)


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow updates the config entry."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_SERIAL,
        data=ENTRY_DATA,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**STANDARD_CONFIG, CONF_HOST: "5.6.7.8"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_HOST]).to_equal("5.6.7.8")


@test.cases(
    test.case("cannot_connect", side_effect=ConnectTimeout("Test error"), error="cannot_connect"),
    test.case("invalid_auth", side_effect=TypeError("Test error"), error="invalid_auth"),
    test.case("unknown", side_effect=Exception("Test error"), error="unknown"),
)
async def reconfigure_errors(
    side_effect: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    qnap_connect: MagicMock = Depends(qnap_connect_fx),
) -> None:
    """Test reconfigure flow shows error on various exceptions."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_SERIAL,
        data=ENTRY_DATA,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    qnap_connect.get_system_stats.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    qnap_connect.get_system_stats.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    qnap_connect: MagicMock = Depends(qnap_connect_fx),
) -> None:
    """Test reconfigure aborts when serial number doesn't match."""
    entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_SERIAL,
        data=ENTRY_DATA,
    )
    entry.add_to_hass(hass)

    qnap_connect.get_system_stats.return_value = {
        "system": {"serial_number": "DIFFERENT_SERIAL", "name": "Other NAS"}
    }

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        STANDARD_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(entry.data[CONF_HOST]).to_equal(TEST_HOST)
