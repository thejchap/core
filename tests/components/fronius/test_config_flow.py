"""Test the fronius config flow."""

from unittest.mock import patch

from pyfronius import FroniusError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fronius.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


INVERTER_INFO_RETURN_VALUE = {
    "inverters": [
        {
            "device_id": {"value": "1"},
            "unique_id": {"value": "1234567"},
        }
    ]
}
LOGGER_INFO_RETURN_VALUE = {"unique_identifier": {"value": "123.4567"}}
MOCK_DHCP_DATA = DhcpServiceInfo(
    hostname="fronius",
    ip="10.2.3.4",
    macaddress="0003ac112233",
)


@fixture
def no_setup_fixture():
    """Disable setting up the whole integration in config_flow tests."""
    with patch(
        "homeassistant.components.fronius.async_setup_entry",
        return_value=True,
    ):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _no_setup: None = Depends(no_setup_fixture),
) -> None:
    """Module-local fixture-resolution anchor."""


async def assert_finish_flow_with_logger(hass: HomeAssistant, flow_id: str) -> None:
    """Assert finishing the flow with a logger device."""
    with patch(
        "pyfronius.Fronius.current_logger_info",
        return_value=LOGGER_INFO_RETURN_VALUE,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {"host": "10.9.8.1"}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SolarNet Datalogger at 10.9.8.1")
    expect(result["data"]).to_equal({"host": "10.9.8.1", "is_logger": True})
    expect(result["result"].unique_id).to_equal("123.4567")


async def assert_abort_flow_with_logger(
    hass: HomeAssistant, flow_id: str, reason: str
):
    """Assert the flow was aborted when a logger device responded."""
    with patch(
        "pyfronius.Fronius.current_logger_info",
        return_value=LOGGER_INFO_RETURN_VALUE,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {"host": "10.9.8.1"}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)
    return result


@test
async def form_with_logger(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the basic flow with a logger device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)
    await assert_finish_flow_with_logger(hass, result["flow_id"])


@test
async def form_with_inverter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the basic flow with a Gen24 device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with (
        patch("pyfronius.Fronius.current_logger_info", side_effect=FroniusError),
        patch(
            "pyfronius.Fronius.inverter_info",
            return_value=INVERTER_INFO_RETURN_VALUE,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "10.9.1.1"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("SolarNet Inverter at 10.9.1.1")
    expect(result2["data"]).to_equal({"host": "10.9.1.1", "is_logger": False})
    expect(result2["result"].unique_id).to_equal("1234567")


@test.cases(
    test.case("error", inverter_side_effect=FroniusError),
    test.case("none", inverter_side_effect=None),
)
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    inverter_side_effect,
) -> None:
    """Test we handle cannot connect error."""
    INVERTER_INFO_NONE: dict[str, list] = {"inverters": []}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch("pyfronius.Fronius.current_logger_info", side_effect=FroniusError),
        patch(
            "pyfronius.Fronius.inverter_info",
            side_effect=inverter_side_effect,
            return_value=INVERTER_INFO_NONE,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
    await assert_finish_flow_with_logger(hass, result2["flow_id"])


@test
async def form_unexpected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("pyfronius.Fronius.current_logger_info", side_effect=KeyError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
    await assert_finish_flow_with_logger(hass, result2["flow_id"])


@test
async def form_already_existing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test existing entry."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=LOGGER_INFO_RETURN_VALUE["unique_identifier"]["value"],
        data={CONF_HOST: "10.9.8.1", "is_logger": True},
    ).add_to_hass(hass)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await assert_abort_flow_with_logger(
        hass, result["flow_id"], reason="already_configured"
    )


@test.skip("requires aioclient_mock + mock_responses() helper for test_init imports")
async def config_flow_already_configured() -> None:
    """Stub for test_config_flow_already_configured (port deferred)."""


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow from discovery."""
    with (
        patch("homeassistant.components.fronius.config_flow.DHCP_REQUEST_DELAY", 0),
        patch(
            "pyfronius.Fronius.current_logger_info",
            return_value=LOGGER_INFO_RETURN_VALUE,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=MOCK_DHCP_DATA
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm_discovery")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"SolarNet Datalogger at {MOCK_DHCP_DATA.ip}")
    expect(result["data"]).to_equal({"host": MOCK_DHCP_DATA.ip, "is_logger": True})
    expect(result["result"].unique_id).to_equal("123.4567")


@test
async def dhcp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow from discovery."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123.4567890",
        data={CONF_HOST: f"http://{MOCK_DHCP_DATA.ip}/", "is_logger": True},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=MOCK_DHCP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_invalid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a flow from discovery."""
    with (
        patch("homeassistant.components.fronius.config_flow.DHCP_REQUEST_DELAY", 0),
        patch("pyfronius.Fronius.current_logger_info", side_effect=FroniusError),
        patch("pyfronius.Fronius.inverter_info", side_effect=FroniusError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=MOCK_DHCP_DATA
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_host")


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring an entry."""
    old_host = "http://10.1.0.1"
    new_host = "http://10.1.0.2"
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1234567",
        data={CONF_HOST: old_host, "is_logger": True},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with (
        patch("pyfronius.Fronius.current_logger_info", side_effect=FroniusError),
        patch(
            "pyfronius.Fronius.inverter_info",
            return_value=INVERTER_INFO_RETURN_VALUE,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"host": new_host}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data).to_equal({"host": new_host, "is_logger": False})


@test
async def reconfigure_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=LOGGER_INFO_RETURN_VALUE["unique_identifier"]["value"],
        data={CONF_HOST: "10.1.2.3", "is_logger": True},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    with (
        patch("pyfronius.Fronius.current_logger_info", side_effect=FroniusError),
        patch("pyfronius.Fronius.inverter_info", side_effect=FroniusError),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    await assert_abort_flow_with_logger(
        hass, result2["flow_id"], reason="reconfigure_successful"
    )


@test
async def reconfigure_unexpected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=LOGGER_INFO_RETURN_VALUE["unique_identifier"]["value"],
        data={CONF_HOST: "10.1.2.3", "is_logger": True},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    with patch("pyfronius.Fronius.current_logger_info", side_effect=KeyError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})

    await assert_abort_flow_with_logger(
        hass, result2["flow_id"], reason="reconfigure_successful"
    )


@test
async def reconfigure_to_different_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring an entry to a different device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="999.9999999",
        data={CONF_HOST: "10.1.2.3", "is_logger": True},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    await assert_abort_flow_with_logger(
        hass, result["flow_id"], reason="unique_id_mismatch"
    )
