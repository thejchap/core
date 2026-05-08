"""Test the Plugwise config flow."""

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
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
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

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    mock_smile_adam,
    mock_smile_config_flow,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

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
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture executor anchor."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    smile: MagicMock = Depends(mock_smile_config_flow),
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
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(smile.connect.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal(TEST_SMILE_HOST)


@test.cases(
    test.case("smile", discovery=TEST_DISCOVERY, username=TEST_USERNAME),
    test.case("stretch", discovery=TEST_DISCOVERY2, username=TEST_USERNAME2),
)
async def zeroconf_flow(
    *,
    discovery: ZeroconfServiceInfo,
    username: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    smile: MagicMock = Depends(mock_smile_config_flow),
) -> None:
    """Test config flow for smile devices via zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")

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
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(smile.connect.mock_calls)).to_equal(1)
    expect(result2["result"].unique_id).to_equal(TEST_SMILE_HOST)


@test
async def zeroconf_flow_stretch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _smile: MagicMock = Depends(mock_smile_config_flow),
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

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: TEST_PASSWORD},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Test Smile Name")


@test
async def zercoconf_discovery_update_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    smile: MagicMock = Depends(mock_smile_config_flow),
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

    smile.connect.side_effect = ConnectionFailedError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("0.0.0.0")

    smile.connect.side_effect = None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DISCOVERY,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("1.1.1.1")


@test.cases(
    test.case("ConnectionFailedError", side_effect=ConnectionFailedError, reason="cannot_connect"),
    test.case("InvalidAuthentication", side_effect=InvalidAuthentication, reason="invalid_auth"),
    test.case("InvalidSetupError", side_effect=InvalidSetupError, reason="invalid_setup"),
    test.case("InvalidXMLError", side_effect=InvalidXMLError, reason="response_error"),
    test.case("RuntimeError", side_effect=RuntimeError, reason="unknown"),
    test.case("UnsupportedDeviceError", side_effect=UnsupportedDeviceError, reason="unsupported"),
)
async def flow_errors(
    *,
    side_effect: type[Exception],
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    smile: MagicMock = Depends(mock_smile_config_flow),
) -> None:
    """Test we handle each exception error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})
    expect(result.get("step_id")).to_equal("user")

    smile.connect.side_effect = side_effect

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": reason})
    expect(result2.get("step_id")).to_equal("user")

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(len(smile.connect.mock_calls)).to_equal(1)

    smile.connect.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST, CONF_PASSWORD: TEST_PASSWORD},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("Test Smile Name")


@test
async def user_abort_existing_anna(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _smile: MagicMock = Depends(mock_smile_config_flow),
) -> None:
    """Test the full user configuration flow aborts with existing entry."""
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _smile: MagicMock = Depends(mock_smile_config_flow),
) -> None:
    """Test zeroconf abort with existing anna."""
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


@test.skip("requires init_integration fixture chain (not yet ported)")
async def zeroconf_abort_anna_with_existing_config_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort Anna discovery with existing config entries."""


@test
async def zeroconf_abort_anna_with_adam(
    _trigger: None = Depends(_trigger_executor),
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


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _smile_adam: MagicMock = Depends(mock_smile_adam),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow."""
    config_entry.add_to_hass(hass)

    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data.get(CONF_HOST)).to_equal(TEST_HOST)


@test
async def reconfigure_flow_smile_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    smile_adam: MagicMock = Depends(mock_smile_adam),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow aborts on other Smile ID."""
    smile_adam.smile.hostname = TEST_SMILE_HOST

    config_entry.add_to_hass(hass)
    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_the_same_smile")


@test.cases(
    test.case("ConnectionFailedError", side_effect=ConnectionFailedError, reason="cannot_connect"),
    test.case("InvalidAuthentication", side_effect=InvalidAuthentication, reason="invalid_auth"),
    test.case("InvalidSetupError", side_effect=InvalidSetupError, reason="invalid_setup"),
    test.case("InvalidXMLError", side_effect=InvalidXMLError, reason="response_error"),
    test.case("RuntimeError", side_effect=RuntimeError, reason="unknown"),
    test.case("UnsupportedDeviceError", side_effect=UnsupportedDeviceError, reason="unsupported"),
)
async def reconfigure_flow_connect_errors(
    *,
    side_effect: type[Exception],
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    smile_adam: MagicMock = Depends(mock_smile_adam),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle each reconfigure exception error and recover."""
    smile_adam.connect.side_effect = side_effect

    config_entry.add_to_hass(hass)
    reconfigure_result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": reason})
    expect(result.get("step_id")).to_equal("reconfigure")

    smile_adam.connect.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data.get(CONF_HOST)).to_equal(TEST_HOST)
