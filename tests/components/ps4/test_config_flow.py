"""Define tests for the PlayStation 4 config flow."""

from unittest.mock import patch

from pyps4_2ndscreen.errors import CredentialTimeout
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components import ps4
from homeassistant.components.ps4.config_flow import LOCAL_UDP_PORT
from homeassistant.components.ps4.const import (
    DEFAULT_ALIAS,
    DEFAULT_NAME,
    DEFAULT_REGION,
    DOMAIN,
)
from homeassistant.const import (
    CONF_CODE,
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_REGION,
    CONF_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import location as location_util

from ._fixtures import location_info, patch_io, ps4_setup

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_TITLE = "PlayStation 4"
MOCK_CODE = 12345678
MOCK_CODE_LEAD_0 = 1234567
MOCK_CODE_LEAD_0_STR = "01234567"
MOCK_CREDS = "000aa000"
MOCK_HOST = "192.0.0.0"
MOCK_HOST_ADDITIONAL = "192.0.0.1"
MOCK_DEVICE = {
    CONF_HOST: MOCK_HOST,
    CONF_NAME: DEFAULT_NAME,
    CONF_REGION: DEFAULT_REGION,
}
MOCK_DEVICE_ADDITIONAL = {
    CONF_HOST: MOCK_HOST_ADDITIONAL,
    CONF_NAME: DEFAULT_NAME,
    CONF_REGION: DEFAULT_REGION,
}
MOCK_CONFIG = {
    CONF_IP_ADDRESS: MOCK_HOST,
    CONF_NAME: DEFAULT_NAME,
    CONF_REGION: DEFAULT_REGION,
    CONF_CODE: MOCK_CODE,
}
MOCK_CONFIG_ADDITIONAL = {
    CONF_IP_ADDRESS: MOCK_HOST_ADDITIONAL,
    CONF_NAME: DEFAULT_NAME,
    CONF_REGION: DEFAULT_REGION,
    CONF_CODE: MOCK_CODE,
}
MOCK_DATA = {CONF_TOKEN: MOCK_CREDS, "devices": [MOCK_DEVICE]}
MOCK_UDP_PORT = 987
MOCK_TCP_PORT = 997

MOCK_AUTO = {"Config Mode": "Auto Discover"}
MOCK_MANUAL = {"Config Mode": "Manual Entry", CONF_IP_ADDRESS: MOCK_HOST}

MOCK_LOCATION = location_util.LocationInfo(
    "0.0.0.0",
    "US",
    "USD",
    "CA",
    "California",
    "San Diego",
    "92122",
    "America/Los_Angeles",
    32.8594,
    -117.2073,
    True,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _io: None = Depends(patch_io),
    _location: None = Depends(location_info),
    _setup: None = Depends(ps4_setup),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test registering an implementation and flow works."""
    # User Step Started, results in Step Creds
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    # Step Creds results with form in Step Mode.
    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    # Step Mode with User Input which is not manual, results in Step Link.
    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")

    # User Input results in created entry.
    with (
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)),
        patch(
            "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_TOKEN]).to_equal(MOCK_CREDS)
    expect(result["data"]["devices"]).to_equal([MOCK_DEVICE])
    expect(result["title"]).to_equal(MOCK_TITLE)


@test
async def multiple_flow_implementation(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test multiple device flows."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")

    with (
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)),
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_TOKEN]).to_equal(MOCK_CREDS)
    expect(result["data"]["devices"]).to_equal([MOCK_DEVICE])
    expect(result["title"]).to_equal(MOCK_TITLE)

    entries = hass.config_entries.async_entries()
    expect(len(entries)).to_equal(1)
    entry_1 = entries[0]
    expect(len(entry_1.data["devices"])).to_equal(1)

    # Test additional flow.
    with (
        patch("pyps4_2ndscreen.Helper.port_bind", return_value=None),
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")

    with (
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG_ADDITIONAL
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_TOKEN]).to_equal(MOCK_CREDS)
    expect(len(result["data"]["devices"])).to_equal(1)
    expect(result["title"]).to_equal(MOCK_TITLE)

    entries = hass.config_entries.async_entries()
    expect(len(entries)).to_equal(2)
    entry_2 = entries[-1]
    expect(len(entry_2.data["devices"])).to_equal(1)
    expect(entry_1 is not entry_2).to_be(True)


@test
async def port_bind_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that flow aborted when cannot bind to ports 987, 997."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=MOCK_UDP_PORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("port_987_bind_error")

    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=MOCK_TCP_PORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("port_997_bind_error")


@test
async def duplicate_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that Flow aborts when found devices already configured."""
    MockConfigEntry(domain=ps4.DOMAIN, data=MOCK_DATA).add_to_hass(hass)

    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def additional_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that Flow can configure another device."""
    entry = MockConfigEntry(domain=ps4.DOMAIN, data=MOCK_DATA)
    entry.add_to_hass(hass)

    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    with patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG_ADDITIONAL
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_TOKEN]).to_equal(MOCK_CREDS)
    expect(len(result["data"]["devices"])).to_equal(1)
    expect(result["title"]).to_equal(MOCK_TITLE)


@test
async def zero_pin(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test Pin with leading '0' is passed correctly."""
    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "creds"},
            data={},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with (
        patch(
            "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
        ),
        patch(
            "homeassistant.components.ps4."
            "config_flow.location_util.async_detect_location_info",
            return_value=MOCK_LOCATION,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_AUTO
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")

    mock_config = MOCK_CONFIG.copy()
    mock_config[CONF_CODE] = MOCK_CODE_LEAD_0
    with (
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)) as mock_call,
        patch(
            "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], mock_config
        )
    mock_call.assert_called_once_with(
        MOCK_HOST, MOCK_CREDS, MOCK_CODE_LEAD_0_STR, DEFAULT_ALIAS, LOCAL_UDP_PORT
    )


@test
async def no_devices_found_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that failure to find devices aborts flow."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch("pyps4_2ndscreen.Helper.has_devices", return_value=[]):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def manual_mode(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test host specified in manual mode is passed to Step Link."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_MANUAL
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")


@test
async def credential_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that failure to get credentials aborts flow."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("credential_error")


@test
async def credential_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that Credential Timeout shows error."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", side_effect=CredentialTimeout):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")
    expect(result["errors"]).to_equal({"base": "credential_timeout"})


@test
async def wrong_pin_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that incorrect pin throws an error."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    with patch("pyps4_2ndscreen.Helper.link", return_value=(True, False)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")
    expect(result["errors"]).to_equal({"base": "login_failed"})


@test
async def device_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test that device not connected or on throws an error."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    with patch(
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )

    with patch("pyps4_2ndscreen.Helper.link", return_value=(False, True)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("link")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def manual_mode_no_ip_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test no IP specified in manual mode throws an error."""
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("creds")

    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"Config Mode": "Manual Entry"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("mode")
    expect(result["errors"]).to_equal({CONF_IP_ADDRESS: "no_ipaddress"})
