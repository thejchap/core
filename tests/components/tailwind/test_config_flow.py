"""Configuration flow tests for the Tailwind integration."""

from ipaddress import ip_address
from unittest.mock import MagicMock

from gotailwind import (
    TailwindAuthenticationError,
    TailwindConnectionError,
    TailwindUnsupportedFirmwareVersionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.tailwind.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_config_entry, mock_setup_entry, mock_tailwind

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
) -> None:
    """Test the full happy path user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("3c:e9:0e:6d:21:84")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        }
    )
    expect(bool(config_entry.options)).to_be(False)


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=TailwindConnectionError,
        expected_error={CONF_HOST: "cannot_connect"},
    ),
    test.case(
        "invalid_auth",
        side_effect=TailwindAuthenticationError,
        expected_error={CONF_TOKEN: "invalid_auth"},
    ),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def user_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailwind: MagicMock = Depends(mock_tailwind),
    *,
    side_effect: type[Exception],
    expected_error: dict[str, str],
) -> None:
    """Test we show user form on a connection error."""
    tailwind.status.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(expected_error)

    tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.2",
            CONF_TOKEN: "123456",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("3c:e9:0e:6d:21:84")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.2",
            CONF_TOKEN: "123456",
        }
    )
    expect(bool(config_entry.options)).to_be(False)


@test
async def user_flow_unsupported_firmware_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailwind: MagicMock = Depends(mock_tailwind),
) -> None:
    """Test configuration flow aborts when the firmware version is not supported."""
    tailwind.status.side_effect = TailwindUnsupportedFirmwareVersionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unsupported_firmware")


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test configuration flow aborts when the device is already configured."""
    config_entry.add_to_hass(hass)
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.127")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.1")
    expect(config_entry.data[CONF_TOKEN]).to_equal("987654")


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
) -> None:
    """Test the zeroconf happy flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="tailwind-3ce90e6d2184.local.",
            name="mock_name",
            properties={
                "device_id": "_3c_e9_e_6d_21_84_",
                "product": "iQ3",
                "SW ver": "10.10",
                "vendor": "tailwind",
            },
            type="mock_type",
        ),
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0].get("flow_id")).to_equal(result["flow_id"])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_TOKEN: "987654"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("3c:e9:0e:6d:21:84")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "987654",
        }
    )
    expect(bool(config_entry.options)).to_be(False)


@test.cases(
    test.case(
        "no_device_id",
        properties={"SW ver": "10.10"},
        expected_reason="no_device_id",
    ),
    test.case(
        "unsupported_firmware",
        properties={"device_id": "_3c_e9_e_6d_21_84_", "SW ver": "0.0"},
        expected_reason="unsupported_firmware",
    ),
)
async def zeroconf_flow_abort_incompatible_properties(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    properties: dict[str, str],
    expected_reason: str,
) -> None:
    """Test the zeroconf aborts when it advertises incompatible data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="tailwind-3ce90e6d2184.local.",
            name="mock_name",
            properties=properties,
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=TailwindConnectionError,
        expected_error={"base": "cannot_connect"},
    ),
    test.case(
        "invalid_auth",
        side_effect=TailwindAuthenticationError,
        expected_error={CONF_TOKEN: "invalid_auth"},
    ),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def zeroconf_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailwind: MagicMock = Depends(mock_tailwind),
    *,
    side_effect: type[Exception],
    expected_error: dict[str, str],
) -> None:
    """Test we show form on a error."""
    tailwind.status.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="tailwind-3ce90e6d2184.local.",
            name="mock_name",
            properties={
                "device_id": "_3c_e9_e_6d_21_84_",
                "product": "iQ3",
                "SW ver": "10.10",
                "vendor": "tailwind",
            },
            type="mock_type",
        ),
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOKEN: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["errors"]).to_equal(expected_error)

    tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOKEN: "123456",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("3c:e9:0e:6d:21:84")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_TOKEN: "123456",
        }
    )
    expect(bool(config_entry.options)).to_be(False)


@test
async def zeroconf_flow_not_discovered_again(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the zeroconf doesn't re-discover an existing device."""
    config_entry.add_to_hass(hass)
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.127")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="tailwind-3ce90e6d2184.local.",
            name="mock_name",
            properties={
                "device_id": "_3c_e9_e_6d_21_84_",
                "product": "iQ3",
                "SW ver": "10.10",
                "vendor": "tailwind",
            },
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.1")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauthentication configuration flow."""
    config_entry.add_to_hass(hass)
    expect(config_entry.data[CONF_TOKEN]).to_equal("123456")

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "987654"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data[CONF_TOKEN]).to_equal("987654")


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=TailwindConnectionError,
        expected_error={"base": "cannot_connect"},
    ),
    test.case(
        "invalid_auth",
        side_effect=TailwindAuthenticationError,
        expected_error={CONF_TOKEN: "invalid_auth"},
    ),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tailwind: MagicMock = Depends(mock_tailwind),
    *,
    side_effect: type[Exception],
    expected_error: dict[str, str],
) -> None:
    """Test we show form on a error."""
    config_entry.add_to_hass(hass)
    tailwind.status.side_effect = side_effect

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOKEN: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal(expected_error)

    tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOKEN: "123456",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tailwind: MagicMock = Depends(mock_tailwind),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfiguration flow updates an existing entry."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.42")
    expect(config_entry.data[CONF_TOKEN]).to_equal("987654")


@test.cases(
    test.case(
        "cannot_connect",
        side_effect=TailwindConnectionError,
        expected_error={CONF_HOST: "cannot_connect"},
    ),
    test.case(
        "invalid_auth",
        side_effect=TailwindAuthenticationError,
        expected_error={CONF_TOKEN: "invalid_auth"},
    ),
    test.case("unknown", side_effect=Exception, expected_error={"base": "unknown"}),
)
async def reconfigure_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tailwind: MagicMock = Depends(mock_tailwind),
    *,
    side_effect: type[Exception],
    expected_error: dict[str, str],
) -> None:
    """Test the reconfiguration flow recovers from errors."""
    config_entry.add_to_hass(hass)
    tailwind.status.side_effect = side_effect

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal(expected_error)

    tailwind.status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_flow_different_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tailwind: MagicMock = Depends(mock_tailwind),
) -> None:
    """Test reconfigure aborts when the new device has a different MAC."""
    config_entry.add_to_hass(hass)
    tailwind.status.return_value = MagicMock(
        mac_address="aa:bb:cc:dd:ee:ff",
        product="iQ3",
    )

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.42",
            CONF_TOKEN: "987654",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("different_device")


@test
async def dhcp_discovery_updates_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery updates config entries."""
    config_entry.add_to_hass(hass)
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.127")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="tailwind-3ce90e6d2184.local.",
            ip="127.0.0.1",
            macaddress="3ce90e6d2184",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.1")


@test
async def dhcp_discovery_ignores_unknown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test DHCP discovery is only used for updates."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="tailwind-3ce90e6d2184.local.",
            ip="127.0.0.1",
            macaddress="3ce90e6d2184",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
