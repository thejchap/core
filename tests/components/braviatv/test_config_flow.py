"""Define tests for the Bravia TV config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from pybravia import (
    BraviaAuthError,
    BraviaConnectionError,
    BraviaError,
    BraviaNotSupported,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.braviatv.const import (
    CONF_NICKNAME,
    CONF_USE_PSK,
    CONF_USE_SSL,
    DOMAIN,
    NICKNAME_PREFIX,
)
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_CLIENT_ID, CONF_HOST, CONF_MAC, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import instance_id
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from tests.common import MockConfigEntry
from tests.components.braviatv._fixtures import mock_setup_entry, mock_zeroconf
from tests.hass_fixtures import hass, mock_network

BRAVIA_SYSTEM_INFO = {
    "product": "TV",
    "region": "XEU",
    "language": "pol",
    "model": "TV-Model",
    "serial": "serial_number",
    "macAddr": "AA:BB:CC:DD:EE:FF",
    "name": "BRAVIA",
    "generation": "5.2.0",
    "area": "POL",
    "cid": "very_unique_string",
}

BRAVIA_SOURCES = [
    {"title": "HDMI 1", "uri": "extInput:hdmi?port=1"},
    {"title": "HDMI 2", "uri": "extInput:hdmi?port=2"},
    {"title": "HDMI 3/ARC", "uri": "extInput:hdmi?port=3"},
    {"title": "HDMI 4", "uri": "extInput:hdmi?port=4"},
    {"title": "AV/Component", "uri": "extInput:component?port=1"},
]

BRAVIA_SSDP = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location="http://bravia-host:52323/dmr.xml",
    upnp={
        ATTR_UPNP_UDN: "uuid:1234",
        ATTR_UPNP_FRIENDLY_NAME: "Living TV",
        ATTR_UPNP_MODEL_NAME: "KE-55XH9096",
        "X_ScalarWebAPI_DeviceInfo": {
            "X_ScalarWebAPI_ServiceList": {
                "X_ScalarWebAPI_ServiceType": [
                    "guide",
                    "system",
                    "audio",
                    "avContent",
                    "videoScreen",
                ],
            },
        },
    },
)

FAKE_BRAVIA_SSDP = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location="http://soundbar-host:52323/dmr.xml",
    upnp={
        ATTR_UPNP_UDN: "uuid:1234",
        ATTR_UPNP_FRIENDLY_NAME: "Sony Audio Device",
        ATTR_UPNP_MODEL_NAME: "HT-S700RF",
        "X_ScalarWebAPI_DeviceInfo": {
            "X_ScalarWebAPI_ServiceList": {
                "X_ScalarWebAPI_ServiceType": ["guide", "system", "audio", "avContent"],
            },
        },
    },
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def show_form(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")


@test
async def ssdp_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the device is discovered."""
    uuid = await instance_id.async_get(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=BRAVIA_SSDP,
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm")

    with (
        patch("pybravia.BraviaClient.connect"),
        patch("pybravia.BraviaClient.pair"),
        patch("pybravia.BraviaClient.set_wol_mode"),
        patch(
            "pybravia.BraviaClient.get_system_info",
            return_value=BRAVIA_SYSTEM_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("authorize")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: False, CONF_USE_SSL: False}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("pin")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["result"].unique_id).to_equal("very_unique_string")
        expect(result["title"]).to_equal("BRAVIA TV-Model")
        expect(result["data"]).to_equal(
            {
                CONF_HOST: "bravia-host",
                CONF_PIN: "1234",
                CONF_USE_PSK: False,
                CONF_USE_SSL: False,
                CONF_MAC: "AA:BB:CC:DD:EE:FF",
                CONF_CLIENT_ID: uuid,
                CONF_NICKNAME: f"{NICKNAME_PREFIX} {uuid[:6]}",
            }
        )


@test
async def ssdp_discovery_fake(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that not Bravia device is not discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=FAKE_BRAVIA_SSDP,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("not_bravia_device")


@test
async def ssdp_discovery_exist(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the existed device is not discovered."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=BRAVIA_SSDP,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_invalid_host(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that errors are shown when the host is invalid."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "invalid/host"}
    )

    expect(result["errors"]).to_equal({CONF_HOST: "invalid_host"})


@test.cases(
    test.case("invalid_auth", BraviaAuthError, "invalid_auth"),
    test.case("unsupported_model", BraviaNotSupported, "unsupported_model"),
    test.case("cannot_connect", BraviaConnectionError, "cannot_connect"),
)
async def pin_form_error(
    side_effect: type[Exception],
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that PIN form errors are correct."""
    with (
        patch(
            "pybravia.BraviaClient.connect",
            side_effect=side_effect,
        ),
        patch("pybravia.BraviaClient.pair"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: False}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        expect(result["errors"]).to_equal({"base": error_message})


@test.cases(
    test.case("invalid_auth", BraviaAuthError, "invalid_auth"),
    test.case("unsupported_model", BraviaNotSupported, "unsupported_model"),
    test.case("cannot_connect", BraviaConnectionError, "cannot_connect"),
)
async def psk_form_error(
    side_effect: type[Exception],
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that PSK form errors are correct."""
    with patch(
        "pybravia.BraviaClient.connect",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: True}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "mypsk"}
        )

        expect(result["errors"]).to_equal({"base": error_message})


@test
async def no_ip_control(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that error are shown when IP Control is disabled on the TV."""
    with patch("pybravia.BraviaClient.pair", side_effect=BraviaError):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: False}
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("no_ip_control")


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that error are shown when duplicates are added."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("pybravia.BraviaClient.connect"),
        patch("pybravia.BraviaClient.pair"),
        patch("pybravia.BraviaClient.set_wol_mode"),
        patch(
            "pybravia.BraviaClient.get_system_info",
            return_value=BRAVIA_SYSTEM_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: False}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("psk_no_ssl", True, False),
    test.case("pin_no_ssl", False, False),
    test.case("psk_ssl", True, True),
    test.case("pin_ssl", False, True),
)
async def create_entry(
    use_psk: bool,
    use_ssl: bool,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that entry is added correctly."""
    uuid = await instance_id.async_get(hass)

    with (
        patch("pybravia.BraviaClient.connect"),
        patch("pybravia.BraviaClient.pair"),
        patch("pybravia.BraviaClient.set_wol_mode"),
        patch(
            "pybravia.BraviaClient.get_system_info",
            return_value=BRAVIA_SYSTEM_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: "bravia-host"}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("authorize")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: use_psk, CONF_USE_SSL: use_ssl}
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("psk" if use_psk else "pin")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "secret"}
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["result"].unique_id).to_equal("very_unique_string")
        expect(result["title"]).to_equal("BRAVIA TV-Model")
        expect(result["data"]).to_equal(
            {
                CONF_HOST: "bravia-host",
                CONF_PIN: "secret",
                CONF_USE_PSK: use_psk,
                CONF_USE_SSL: use_ssl,
                CONF_MAC: "AA:BB:CC:DD:EE:FF",
                **(
                    {
                        CONF_CLIENT_ID: uuid,
                        CONF_NICKNAME: f"{NICKNAME_PREFIX} {uuid[:6]}",
                    }
                    if not use_psk
                    else {}
                ),
            }
        )


@test.cases(
    test.case("psk", True, "7777"),
    test.case("pin", False, "newpsk"),
)
async def reauth_successful(
    use_psk: bool,
    new_pin: str,
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test that the reauthorization is successful."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="very_unique_string",
        data={
            CONF_HOST: "bravia-host",
            CONF_PIN: "1234",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
        },
        title="TV-Model",
    )
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("authorize")

    with (
        patch("pybravia.BraviaClient.connect"),
        patch(
            "pybravia.BraviaClient.get_power_status",
            return_value="active",
        ),
        patch(
            "pybravia.BraviaClient.get_external_status",
            return_value=BRAVIA_SOURCES,
        ),
        patch(
            "pybravia.BraviaClient.send_rest_req",
            return_value={},
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_USE_PSK: use_psk}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: new_pin}
        )

        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(config_entry.data[CONF_PIN]).to_equal(new_pin)
