"""Tests for the WLED config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
from wled import WLEDConnectionError, WLEDUnsupportedVersionError

from homeassistant.components.wled.const import CONF_KEEP_MAIN_LIGHT, DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_onboarding,
    mock_setup_entry,
    mock_wled,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {CONF_HOST: "10.10.0.10"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("ip", host_input="192.168.1.123"),
    test.case("http", host_input="http://192.168.1.123"),
    test.case("https_path", host_input="https://192.168.1.123/settings"),
    test.case("https_port_path", host_input="https://192.168.1.123:80/settings"),
)
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _wled: MagicMock = Depends(mock_wled),
    *,
    host_input: str,
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: host_input}
    )

    expect(result.get("title")).to_equal("WLED RGB Light")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect(result["result"].unique_id).to_equal("aabbccddeeff")


@test
async def full_reconfigure_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _wled: MagicMock = Depends(mock_wled),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full reconfigure flow from start to finish."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("10.10.0.10")


@test
async def full_reconfigure_flow_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    wled: MagicMock = Depends(mock_wled),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration failure when the unique ID changes."""
    config_entry.add_to_hass(hass)

    device = wled.update.return_value
    device.info.mac_address = "invalid"

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("unique_id_mismatch")


@test
async def full_reconfigure_flow_connection_error_and_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    wled: MagicMock = Depends(mock_wled),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we show user form on WLED connection error and allows user to change host."""
    config_entry.add_to_hass(hass)

    wled.update.side_effect = WLEDConnectionError

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})

    wled.update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("10.10.0.10")


@test
async def full_zeroconf_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _wled: MagicMock = Depends(mock_wled),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    expect(flows[0].get("context", {}).get("configuration_url")).to_equal(
        "http://192.168.1.123"
    )
    expect(result.get("description_placeholders")).to_equal(
        {CONF_NAME: "WLED RGB Light"}
    )
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2.get("title")).to_equal("WLED RGB Light")
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect("data" in result2).to_be(True)
    expect(result2["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result2).to_be(True)
    expect(result2["result"].unique_id).to_equal("aabbccddeeff")


@test
async def zeroconf_during_onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _wled: MagicMock = Depends(mock_wled),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    onboarding: MagicMock = Depends(mock_onboarding),
) -> None:
    """Test we create a config entry when discovered during onboarding."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    expect(result.get("title")).to_equal("WLED RGB Light")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect(result.get("data")).to_equal({CONF_HOST: "192.168.1.123"})
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("aabbccddeeff")

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(onboarding.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "cannot_connect",
        exception=WLEDConnectionError,
        errors={"base": "cannot_connect"},
    ),
    test.case(
        "unsupported_version",
        exception=WLEDUnsupportedVersionError,
        errors={"base": "unsupported_version"},
    ),
)
async def form_submission_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wled: MagicMock = Depends(mock_wled),
    *,
    exception: type[Exception],
    errors: dict,
) -> None:
    """Test errors during form submission."""
    wled.update.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=CONFIG,
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal(errors)


@test
async def zeroconf_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wled: MagicMock = Depends(mock_wled),
) -> None:
    """Test we abort zeroconf flow on WLED connection error."""
    wled.update.side_effect = WLEDConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def zeroconf_unsupported_version_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    wled: MagicMock = Depends(mock_wled),
) -> None:
    """Test we abort zeroconf flow on WLED unsupported version error."""
    wled.update.side_effect = WLEDUnsupportedVersionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("unsupported_version")


@test.cases(
    test.case("lower", device_mac="aabbccddeeff"),
    test.case("upper", device_mac="AABBCCDDEEFF"),
)
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    wled: MagicMock = Depends(mock_wled),
    *,
    device_mac: str,
) -> None:
    """Test we abort zeroconf flow if WLED device already configured."""
    wled.update.return_value.info.mac_address = device_mac
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "192.168.1.123"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_without_mac_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _wled: MagicMock = Depends(mock_wled),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort zeroconf flow if WLED device already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case("lower", device_mac="aabbccddeeff"),
    test.case("upper", device_mac="AABBCCDDEEFF"),
)
async def zeroconf_with_mac_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _wled: MagicMock = Depends(mock_wled),
    *,
    device_mac: str,
) -> None:
    """Test we abort zeroconf flow if WLED device already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: device_mac},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _wled: MagicMock = Depends(mock_wled),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options config flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("init")

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_KEEP_MAIN_LIGHT: True},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("data")).to_equal(
        {
            CONF_KEEP_MAIN_LIGHT: True,
        }
    )
