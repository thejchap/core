"""Test the devolo Home Network config flow."""

from unittest.mock import patch

from devolo_plc_api.exceptions.device import DeviceNotFound, DevicePasswordProtected
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.devolo_home_network.const import (
    DOMAIN,
    SERIAL_NUMBER,
    TITLE,
)
from homeassistant.const import CONF_BASE, CONF_IP_ADDRESS, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import configure_integration
from ._fixtures import devolo_zeroconf, info, mock_device
from .const import (
    DISCOVERY_INFO,
    DISCOVERY_INFO_CHANGED,
    DISCOVERY_INFO_WRONG_DEVICE,
    IP,
    IP_ALT,
)
from .mock import MockDevice, MockDeviceWrongPassword

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _zc: None = Depends(devolo_zeroconf),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def form(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    info_: dict[str, str] = Depends(info),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.devolo_home_network.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_IP_ADDRESS: IP, CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["result"].unique_id).to_equal(info_[SERIAL_NUMBER])
    expect(result2["title"]).to_equal(info_[TITLE])
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: IP,
            CONF_PASSWORD: "",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "device_not_found",
        exception_type=DeviceNotFound(IP),
        expected_error="cannot_connect",
    ),
    test.case(
        "password_protected",
        exception_type=DevicePasswordProtected,
        expected_error="invalid_auth",
    ),
    test.case(
        "unknown",
        exception_type=Exception,
        expected_error="unknown",
    ),
)
async def form_error(
    *,
    exception_type: object,
    expected_error: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.devolo_home_network.config_flow.validate_input",
        side_effect=exception_type,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_IP_ADDRESS: IP, CONF_PASSWORD: ""},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_BASE: expected_error})

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDevice,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_IP_ADDRESS: IP, CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["description_placeholders"]).to_equal({"host_name": "test"})

    context = next(
        flow["context"]
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )

    expect(context["title_placeholders"][CONF_NAME]).to_equal(
        DISCOVERY_INFO.hostname.split(".", maxsplit=1)[0]
    )

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDevice,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["title"]).to_equal("test")
    expect(result2["data"]).to_equal(
        {
            CONF_IP_ADDRESS: IP,
            CONF_PASSWORD: "",
        }
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["result"].unique_id).to_equal("1234567890")


@test
async def zeroconf_wrong_auth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the zeroconf form asks for password if authorization fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDeviceWrongPassword,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_BASE: "invalid_auth"})

    with (
        patch(
            "homeassistant.components.devolo_home_network.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.devolo_home_network.config_flow.Device",
            new=MockDevice,
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PASSWORD: "new-password"},
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def abort_zeroconf_wrong_device(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort zeroconf for wrong devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_WRONG_DEVICE,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("home_control")


@test
async def abort_if_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _info: dict[str, str] = Depends(info),
) -> None:
    """Test we abort config flow if already configured."""
    entry = configure_integration(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_IP_ADDRESS: IP},
    )
    await hass.async_block_till_done()
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_CHANGED,
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal(IP_ALT)


@test.skip("reauth flow needs mock_zeroconf fixture not in shim")
async def form_reauth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the reauth confirmation form is served."""
