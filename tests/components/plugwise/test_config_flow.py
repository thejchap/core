"""Test the Plugwise config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from plugwise.exceptions import (
    ConnectionFailedError,
    InvalidAuthentication,
    InvalidSetupError,
    InvalidXMLError,
    UnsupportedDeviceError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.plugwise.const import DEFAULT_PORT, DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF, ConfigFlowResult
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SOURCE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    init_integration as init_integration_fx,
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_setup_entry as mock_setup_entry_fx,
    mock_smile_adam as mock_smile_adam_fx,
    mock_smile_config_flow as mock_smile_config_flow_fx,
)


TEST_HOST = "1.1.1.1"
TEST_HOSTNAME = "smileabcdef"
TEST_HOSTNAME2 = "stretchabc"
TEST_PASSWORD = "test_password"
TEST_PORT = 81
TEST_USERNAME = "smile"
TEST_USERNAME2 = "stretch"
TEST_SMILE_HOST = "smile12345"

TEST_DISCOVERY = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_HOST),
    ip_addresses=[ip_address(TEST_HOST)],
    hostname=f"{TEST_HOSTNAME}-2.local.",
    name="mock_name",
    port=DEFAULT_PORT,
    properties={
        "product": "smile",
        "version": "1.2.3",
        "hostname": f"{TEST_HOSTNAME}.local.",
    },
    type="mock_type",
)

TEST_DISCOVERY2 = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_HOST),
    ip_addresses=[ip_address(TEST_HOST)],
    hostname=f"{TEST_HOSTNAME2}.local.",
    name="mock_name",
    port=DEFAULT_PORT,
    properties={
        "product": "stretch",
        "version": "1.2.3",
        "hostname": f"{TEST_HOSTNAME2}.local.",
    },
    type="mock_type",
)

TEST_DISCOVERY_ANNA = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_HOST),
    ip_addresses=[ip_address(TEST_HOST)],
    hostname=f"{TEST_HOSTNAME}.local.",
    name="mock_name",
    port=DEFAULT_PORT,
    properties={
        "product": "smile_thermo",
        "version": "1.2.3",
        "hostname": f"{TEST_HOSTNAME}.local.",
    },
    type="mock_type",
)

TEST_DISCOVERY_ADAM = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_HOST),
    ip_addresses=[ip_address(TEST_HOST)],
    hostname=f"{TEST_HOSTNAME2}.local.",
    name="mock_name",
    port=DEFAULT_PORT,
    properties={
        "product": "smile_open_therm",
        "version": "1.2.3",
        "hostname": f"{TEST_HOSTNAME2}.local.",
    },
    type="mock_type",
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network and mock_async_zeroconf for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Test Smile Name")
    expect(result2.get("data")).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: DEFAULT_PORT,
            CONF_USERNAME: TEST_USERNAME,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_smile_config_flow.connect.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal(TEST_SMILE_HOST)


@test.cases(
    test.case("smile", TEST_DISCOVERY, TEST_USERNAME),
    test.case("stretch", TEST_DISCOVERY2, TEST_USERNAME2),
)
async def zeroconf_flow(
    discovery: ZeroconfServiceInfo,
    username: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test config flow for smile devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")
    expect("flow_id" in result).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: TEST_PASSWORD},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Test Smile Name")
    expect(result2.get("data")).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: DEFAULT_PORT,
            CONF_USERNAME: TEST_USERNAME,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_smile_config_flow.connect.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal(TEST_SMILE_HOST)


@test
async def zeroconf_flow_stretch(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test config flow for stretch devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY2,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")
    expect("flow_id" in result).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: TEST_PASSWORD},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Test Smile Name")
    expect(result2.get("data")).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: DEFAULT_PORT,
            CONF_USERNAME: TEST_USERNAME2,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_smile_config_flow.connect.mock_calls)).to_equal(1)


@test
async def zeroconf_discovery_update_configuration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test if a discovered device is configured and updated with new host."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=CONF_NAME,
        data={
            CONF_HOST: "0.0.0.0",
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
        unique_id=TEST_HOSTNAME,
    )
    entry.add_to_hass(hass)

    expect(entry.data[CONF_HOST]).to_equal("0.0.0.0")

    mock_smile_config_flow.connect.side_effect = ConnectionFailedError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("0.0.0.0")

    mock_smile_config_flow.connect.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")


@test.cases(
    test.case("connect", ConnectionFailedError, "cannot_connect"),
    test.case("auth", InvalidAuthentication, "invalid_auth"),
    test.case("setup", InvalidSetupError, "invalid_setup"),
    test.case("xml", InvalidXMLError, "response_error"),
    test.case("runtime", RuntimeError, "unknown"),
    test.case("unsupported", UnsupportedDeviceError, "unsupported"),
)
async def flow_errors(
    side_effect: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test we handle each exception error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")
    expect("flow_id" in result).to_be(True)

    mock_smile_config_flow.connect.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": reason})
    expect(result2.get("step_id")).to_equal("user")

    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(mock_smile_config_flow.connect.mock_calls)).to_equal(1)

    mock_smile_config_flow.connect.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("Test Smile Name")
    expect(result3.get("data")).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: DEFAULT_PORT,
            CONF_USERNAME: TEST_USERNAME,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_smile_config_flow.connect.mock_calls)).to_equal(2)


@test
async def user_abort_existing_anna(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test the full user configuration flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=CONF_NAME,
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
        unique_id=TEST_SMILE_HOST,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: TEST_HOST,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")


@test
async def zeroconf_abort_existing_anna(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_smile_config_flow: MagicMock = Depends(mock_smile_config_flow_fx),
) -> None:
    """Test the full user configuration flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=CONF_NAME,
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
        unique_id=TEST_HOSTNAME,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_abort_anna_with_existing_config_entries(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_smile_adam: MagicMock = Depends(mock_smile_adam_fx),
    init_integration: MockConfigEntry = Depends(init_integration_fx),
) -> None:
    """Test we abort Anna discovery with existing config entries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("anna_with_adam")


@test
async def zeroconf_abort_anna_with_adam(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort Anna discovery when an Adam is also discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    expect(len(flows_in_progress)).to_equal(1)
    expect(list(flows_in_progress)[0].product).to_equal("smile_thermo")

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ADAM,
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")

    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    expect(len(flows_in_progress)).to_equal(1)
    expect(list(flows_in_progress)[0].product).to_equal("smile_open_therm")

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY_ANNA,
    )
    expect(result3.get("type")).to_be(FlowResultType.ABORT)
    expect(result3.get("reason")).to_equal("anna_with_adam")

    flows_in_progress = hass.config_entries.flow._handler_progress_index[DOMAIN]
    expect(len(flows_in_progress)).to_equal(1)
    expect(list(flows_in_progress)[0].product).to_equal("smile_open_therm")


async def _start_reconfigure_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    host_ip: str,
) -> ConfigFlowResult:
    """Initialize a reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    reconfigure_result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")

    return await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: host_ip}
    )


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_smile_adam: AsyncMock = Depends(mock_smile_adam_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow."""
    result = await _start_reconfigure_flow(hass, mock_config_entry, TEST_HOST)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data.get(CONF_HOST)).to_equal(TEST_HOST)


@test
async def reconfigure_flow_smile_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_smile_adam: AsyncMock = Depends(mock_smile_adam_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow aborts on other Smile ID."""
    mock_smile_adam.smile.hostname = TEST_SMILE_HOST

    result = await _start_reconfigure_flow(hass, mock_config_entry, TEST_HOST)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_the_same_smile")


@test.cases(
    test.case("connect", ConnectionFailedError, "cannot_connect"),
    test.case("auth", InvalidAuthentication, "invalid_auth"),
    test.case("setup", InvalidSetupError, "invalid_setup"),
    test.case("xml", InvalidXMLError, "response_error"),
    test.case("runtime", RuntimeError, "unknown"),
    test.case("unsupported", UnsupportedDeviceError, "unsupported"),
)
async def reconfigure_flow_connect_errors(
    side_effect: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_smile_adam: AsyncMock = Depends(mock_smile_adam_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we handle each reconfigure exception error and recover."""
    mock_smile_adam.connect.side_effect = side_effect

    result = await _start_reconfigure_flow(hass, mock_config_entry, TEST_HOST)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": reason})
    expect(result.get("step_id")).to_equal("reconfigure")

    mock_smile_adam.connect.side_effect = None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")

    expect(mock_config_entry.data.get(CONF_HOST)).to_equal(TEST_HOST)
