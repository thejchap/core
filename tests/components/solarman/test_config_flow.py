"""Test the Solarman config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.solarman.const import CONF_SN, DOMAIN, MODEL_NAME_MAP
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    TEST_DEVICE_SN,
    TEST_HOST,
    TEST_MODEL,
    mock_config_entry_sp2w,
    mock_solarman_p1_2w,
    mock_solarman_sp2w,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _solarman: AsyncMock = Depends(mock_solarman_p1_2w),
) -> None:
    """Test successful configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"P1 Meter Reader ({TEST_HOST})")
    expect(result["context"]["unique_id"]).to_equal("SN2345678901")

    data = result["data"]
    expect(data[CONF_HOST]).to_equal(TEST_HOST)
    expect(data[CONF_SN]).to_equal("SN2345678901")
    expect(data[CONF_MODEL]).to_equal("P1-2W")


@test.cases(
    test.case("timeout", exception=TimeoutError, expected_error="timeout"),
    test.case(
        "cannot_connect", exception=ConnectionError, expected_error="cannot_connect"
    ),
    test.case(
        "unknown", exception=Exception("Some unknown error"), expected_error="unknown"
    ),
)
async def flow_error(
    exception: Exception,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test connection error handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    solarman.get_config.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(expected_error)

    solarman.get_config.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: TEST_HOST},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry_sp2w),
    _solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test duplicate entry handling."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test zeroconf discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            name="mock_name",
            port=8080,
            hostname="mock_hostname",
            type="_solarman._tcp.local.",
            properties={"product_type": "SP-2W-EU", "serial": TEST_DEVICE_SN},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{MODEL_NAME_MAP[TEST_MODEL]} ({TEST_HOST})")

    data = result["data"]
    expect(data[CONF_HOST]).to_equal(TEST_HOST)
    expect(data[CONF_SN]).to_equal(TEST_DEVICE_SN)
    expect(data[CONF_MODEL]).to_equal(TEST_MODEL)
    expect(result["context"]["unique_id"]).to_equal(TEST_DEVICE_SN)


@test
async def zeroconf_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry_sp2w),
    _solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test zeroconf discovery when already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            name="mock_name",
            port=8080,
            hostname="mock_hostname",
            type="_solarman._tcp.local.",
            properties={"product_type": "SP-2W-EU", "serial": TEST_DEVICE_SN},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_ip_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry_sp2w),
    _solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test discovery setup updates new config data."""
    entry.add_to_hass(hass)

    expect(entry.data[CONF_HOST]).to_equal(TEST_HOST)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.101"),
            ip_addresses=[ip_address("192.168.1.101")],
            name="mock_name",
            port=8080,
            hostname="mock_hostname",
            type="_solarman._tcp.local.",
            properties={"product_type": "SP-2W-EU", "serial": TEST_DEVICE_SN},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data[CONF_HOST]).to_equal("192.168.1.101")


@test.cases(
    test.case("timeout", exception=TimeoutError, expected_error="timeout"),
    test.case(
        "cannot_connect", exception=ConnectionError, expected_error="cannot_connect"
    ),
    test.case(
        "unknown", exception=Exception("Some unknown error"), expected_error="unknown"
    ),
)
async def zeroconf_error(
    exception: Exception,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    solarman: AsyncMock = Depends(mock_solarman_sp2w),
) -> None:
    """Test discovery setup."""
    solarman.get_config.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(TEST_HOST),
            ip_addresses=[ip_address(TEST_HOST)],
            name="mock_name",
            port=8080,
            hostname="mock_hostname",
            type="_solarman._tcp.local.",
            properties={"product_type": "SP-2W-EU", "serial": TEST_DEVICE_SN},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_error)
