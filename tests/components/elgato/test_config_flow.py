"""Tests for the Elgato Key Light config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from elgato import ElgatoConnectionError, ElgatoError
from tryke import Depends, expect, fixture, test

from homeassistant.components.elgato.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.elgato._fixtures import (
    mock_config_entry,
    mock_elgato,
    mock_onboarding,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network

mock_zeroconf = mock_zeroconf  # noqa: F811
mock_network = mock_network  # noqa: F811


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_user_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.1"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("CN11A1A00001")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_MAC: None},
    )
    expect(bool(config_entry.options)).to_be(False)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_elgato.info.mock_calls)).to_equal(1)


@test
async def full_zeroconf_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the zeroconf flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="mock_name",
            port=9123,
            properties={"id": "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )

    expect(result["description_placeholders"]).to_equal(
        {"serial_number": "CN11A1A00001"}
    )
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    progress = hass.config_entries.flow.async_progress()
    expect(len(progress)).to_equal(1)
    expect(progress[0].get("flow_id")).to_equal(result["flow_id"])
    expect("context" in progress[0]).to_be(True)
    expect(progress[0]["context"].get("confirm_only")).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("CN11A1A00001")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    expect(bool(config_entry.options)).to_be(False)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_elgato.info.mock_calls)).to_equal(1)


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test we show user form on Elgato Key Light connection error."""
    mock_elgato.info.side_effect = ElgatoConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})
    expect(result["step_id"]).to_equal("user")

    mock_elgato.info.side_effect = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.2"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("CN11A1A00001")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.2", CONF_MAC: None},
    )
    expect(bool(config_entry.options)).to_be(False)


@test
async def zeroconf_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test we abort zeroconf flow on Elgato Key Light connection error."""
    mock_elgato.info.side_effect = ElgatoConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=9123,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["reason"]).to_equal("cannot_connect")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def user_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test we abort user flow if Elgato Key Light device already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test we abort zeroconf flow if Elgato Key Light device already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="mock_name",
            port=9123,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].data[CONF_HOST]).to_equal("127.0.0.1")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.2"),
            ip_addresses=[ip_address("127.0.0.2")],
            hostname="mock_hostname",
            name="mock_name",
            port=9123,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].data[CONF_HOST]).to_equal("127.0.0.2")


@test
async def zeroconf_during_onboarding(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_onboarding: MagicMock = Depends(mock_onboarding),
) -> None:
    """Test the zeroconf creates an entry during onboarding."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="mock_name",
            port=9123,
            properties={"id": "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal("CN11A1A00001")
    expect(config_entry.data).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_MAC: "AA:BB:CC:DD:EE:FF"},
    )
    expect(bool(config_entry.options)).to_be(False)

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_elgato.info.mock_calls)).to_equal(1)
    expect(len(mock_onboarding.mock_calls)).to_equal(1)


@test
async def dhcp_discovery_updates_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test DHCP discovery of a known device updates its stored host."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="elgato",
            ip="127.0.0.42",
            macaddress="aabbccddeeff",
        ),
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.42")


@test
async def dhcp_discovery_same_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test DHCP discovery does nothing when the host is already up to date."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="elgato",
            ip="127.0.0.1",
            macaddress="aabbccddeeff",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.1")


@test
async def dhcp_discovery_no_match(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test DHCP discovery aborts when no matching entry is configured."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="elgato",
            ip="127.0.0.42",
            macaddress="001122334455",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.1")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_elgato: MagicMock = Depends(mock_elgato),
) -> None:
    """Test reconfiguring an existing Elgato device."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.42"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.42")


@test
async def reconfigure_flow_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow recovers from a connection error."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    mock_elgato.info.side_effect = ElgatoError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.42"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_elgato.info.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.42"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_flow_different_device(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_elgato: MagicMock = Depends(mock_elgato),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure aborts when the device at the new host has a different serial."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    mock_elgato.info.return_value.serial_number = "DIFFERENT_SERIAL"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.42"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("different_device")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.1")
