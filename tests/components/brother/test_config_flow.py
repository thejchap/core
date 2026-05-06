"""Define tests for the Brother Printer config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from brother import SnmpError, UnsupportedModelError
from tryke import Depends, expect, fixture, test

from homeassistant.components.brother.const import (
    CONF_COMMUNITY,
    DOMAIN,
    SECTION_ADVANCED_SETTINGS,
)
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.brother import init_integration
from tests.components.brother._fixtures import (
    mock_brother,
    mock_brother_client,
    mock_config_entry,
    mock_setup_entry,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network

CONFIG = {
    CONF_HOST: "127.0.0.1",
    CONF_TYPE: "laser",
    SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
}


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("hostname", "example.local"),
    test.case("ipv4", "127.0.0.1"),
    test.case("ipv6", "2001:db8::1428:57ab"),
)
async def create_entry(
    host: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the user step works with printer hostname/IPv4/IPv6."""
    config = CONFIG.copy()
    config[CONF_HOST] = host

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=config,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("HL-L2340DW 0123456789")
    expect(result["data"][CONF_HOST]).to_equal(host)
    expect(result["data"][CONF_TYPE]).to_equal("laser")
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT]).to_equal(161)
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY]).to_equal("public")
    expect(result["result"].unique_id).to_equal("0123456789")


@test
async def invalid_hostname(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test invalid hostname in user_input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "invalid/hostname",
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({CONF_HOST: "wrong_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("HL-L2340DW 0123456789")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.1")
    expect(result["data"][CONF_TYPE]).to_equal("laser")
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT]).to_equal(161)
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY]).to_equal("public")
    expect(result["result"].unique_id).to_equal("0123456789")


@test.cases(
    test.case("connection_error", ConnectionError(), "cannot_connect"),
    test.case("timeout_error", TimeoutError(), "cannot_connect"),
    test.case("snmp_error", SnmpError("SNMP error"), "snmp_error"),
)
async def errors(
    exc: Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test connection to host error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_brother_client.async_update.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": base_error})

    mock_brother_client.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("HL-L2340DW 0123456789")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.1")
    expect(result["data"][CONF_TYPE]).to_equal("laser")
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT]).to_equal(161)
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY]).to_equal("public")
    expect(result["result"].unique_id).to_equal("0123456789")


@test
async def unsupported_model_error(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother: AsyncMock = Depends(mock_brother),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test unsupported printer model error."""
    mock_brother.create.side_effect = UnsupportedModelError("error")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unsupported_model")


@test
async def device_exists_abort(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort config flow if Brother printer already configured."""
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("connection_error", ConnectionError()),
    test.case("timeout_error", TimeoutError()),
    test.case("snmp_error", SnmpError("error")),
)
async def zeroconf_exception(
    exc: Exception,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort zeroconf flow on exception."""
    mock_brother_client.async_update.side_effect = exc

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def zeroconf_unsupported_model(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother: AsyncMock = Depends(mock_brother),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test unsupported printer model error."""
    mock_brother.create.side_effect = UnsupportedModelError("error")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={"product": "MFC-8660DN"},
            type="mock_type",
        ),
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("unsupported_model")


@test
async def zeroconf_device_exists_abort(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we abort zeroconf flow if Brother printer already configured."""
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    expect(mock_config_entry.data[CONF_HOST]).to_equal("127.0.0.1")


@test
async def zeroconf_no_probe_existing_device(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test we do not probe the device is the host is already configured."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="0123456789", data=CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={},
            type="mock_type",
        ),
    )
    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
    mock_brother_client.async_update.assert_not_called()


@test
async def zeroconf_confirm_create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test zeroconf confirmation and create config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["description_placeholders"]["model"]).to_equal("HL-L2340DW")
    expect(result["description_placeholders"]["serial_number"]).to_equal("0123456789")
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("HL-L2340DW 0123456789")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.1")
    expect(result["data"][CONF_TYPE]).to_equal("laser")
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT]).to_equal(161)
    expect(result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY]).to_equal("public")
    expect(result["result"].unique_id).to_equal("0123456789")


@test
async def reconfigure_successful(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test starting a reconfigure flow."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_HOST: "10.10.10.10",
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        }
    )


@test.cases(
    test.case("connection_error", ConnectionError(), "cannot_connect"),
    test.case("timeout_error", TimeoutError(), "cannot_connect"),
    test.case("snmp_error", SnmpError("error"), "snmp_error"),
)
async def reconfigure_not_successful(
    exc: Exception,
    base_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test starting a reconfigure flow but no connection found."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_brother_client.async_update.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": base_error})

    mock_brother_client.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_HOST: "10.10.10.10",
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        }
    )


@test
async def reconfigure_invalid_hostname(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test starting a reconfigure flow but no connection found."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "invalid/hostname",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({CONF_HOST: "wrong_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_HOST: "10.10.10.10",
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        }
    )


@test
async def reconfigure_not_the_same_device(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test starting the reconfiguration process, but with a different printer."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_brother_client.serial = "9876543210"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "another_device"})

    mock_brother_client.serial = "0123456789"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "11.11.11.11",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_HOST: "11.11.11.11",
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        }
    )
