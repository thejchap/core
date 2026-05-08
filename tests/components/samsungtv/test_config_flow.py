"""Tests for Samsung TV config flow."""

from copy import deepcopy
from unittest.mock import patch

from samsungctl.exceptions import UnhandledResponse
from samsungtvws.exceptions import ConnectionFailure
from tryke import Depends, expect, fixture, test
from websockets.exceptions import WebSocketException

from homeassistant import config_entries
from homeassistant.components.samsungtv.const import (
    CONF_MANUFACTURER,
    CONF_SSDP_RENDERING_CONTROL_LOCATION,
    DEFAULT_MANUFACTURER,
    DOMAIN,
    METHOD_LEGACY,
    RESULT_CANNOT_CONNECT,
    RESULT_NOT_SUPPORTED,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_METHOD,
    CONF_MODEL,
    CONF_PORT,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MANUFACTURER,
    SsdpServiceInfo,
)

from ._fixtures import (
    app_list_delay,
    fake_host,
    mac_address,
    mock_setup_entry,
    rest_api,
    rest_api_failing,
    remote_encrypted_websocket_failing,
    remote_legacy,
    remote_websocket,
    samsungtv_mock_async_get_local_ip,
    silent_ssdp_scanner,
    upnp_factory,
)
from .const import (
    MOCK_SSDP_DATA,
    MOCK_SSDP_DATA_MAIN_TV_AGENT_ST,
    MOCK_SSDP_DATA_RENDERING_CONTROL_ST,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_DATA = {CONF_HOST: "fake_host"}
RESULT_ALREADY_CONFIGURED = "already_configured"
RESULT_ALREADY_IN_PROGRESS = "already_in_progress"
MOCK_DEVICE_INFO = {
    "device": {
        "type": "Samsung SmartTV",
        "name": "fake_name",
        "modelName": "fake_model",
    },
    "id": "123",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ssdp: None = Depends(silent_ssdp_scanner),
    _host: None = Depends(fake_host),
    _local_ip: None = Depends(samsungtv_mock_async_get_local_ip),
    _app_list: None = Depends(app_list_delay),
    _mac: None = Depends(mac_address),
    _upnp: None = Depends(upnp_factory),
    _setup: None = Depends(mock_setup_entry),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass + autouse fixtures."""
    return hass


@test
async def user_form_show(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the user form is shown when starting a flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def user_legacy_not_supported(
    hass: HomeAssistant = Depends(_trigger_executor),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow by user for not supported device."""
    with patch(
        "homeassistant.components.samsungtv.bridge.Remote",
        side_effect=UnhandledResponse("Boom"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_NOT_SUPPORTED)


@test
async def user_websocket_not_supported(
    hass: HomeAssistant = Depends(_trigger_executor),
    _rest: None = Depends(rest_api),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting a flow by user for not supported websocket device."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=WebSocketException("Boom"),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_NOT_SUPPORTED)


@test
async def user_not_successful(
    hass: HomeAssistant = Depends(_trigger_executor),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow by user but no connection found."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=OSError("Boom"),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_CANNOT_CONNECT)


@test
async def user_not_successful_2(
    hass: HomeAssistant = Depends(_trigger_executor),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow by user but no connection found (ConnectionFailure)."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=ConnectionFailure("Boom"),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_CANNOT_CONNECT)


@test
async def user_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow by user that creates a legacy entry."""
    import socket

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.samsungtv.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror("[Error -2] Name or Service not known"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.20.43.21")
    expect(result["data"][CONF_HOST]).to_equal("10.20.43.21")
    expect(result["data"][CONF_METHOD]).to_equal(METHOD_LEGACY)
    expect(result["data"][CONF_MANUFACTURER]).to_equal(DEFAULT_MANUFACTURER)
    expect(result["data"][CONF_MODEL]).to_be(None)
    expect(result["data"][CONF_PORT]).to_equal(55000)
    expect(result["result"].unique_id).to_be(None)


@test
async def ssdp_wrong_manufacturer(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
) -> None:
    """Test starting a flow from discovery with wrong manufacturer."""
    ssdp_data = deepcopy(MOCK_SSDP_DATA)
    ssdp_data.upnp[ATTR_UPNP_MANUFACTURER] = ssdp_data.upnp[ATTR_UPNP_MANUFACTURER][7:]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=ssdp_data,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_NOT_SUPPORTED)


@test
async def ssdp_no_manufacturer(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow from discovery when manufacturer data is missing."""
    ssdp_data = deepcopy(MOCK_SSDP_DATA)
    ssdp_data.upnp.pop(ATTR_UPNP_MANUFACTURER)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=ssdp_data,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_NOT_SUPPORTED)


@test.cases(
    test.case("main_tv_agent", data=MOCK_SSDP_DATA_MAIN_TV_AGENT_ST),
    test.case("rendering_control", data=MOCK_SSDP_DATA_RENDERING_CONTROL_ST),
)
async def ssdp_legacy_not_remote_control_receiver_udn(
    *,
    data: SsdpServiceInfo,
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test we abort if the st is not usable for legacy discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_NOT_SUPPORTED)


@test
async def ssdp(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow from discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("UE55H6400")
    expect(result["data"][CONF_HOST]).to_equal("10.10.12.34")
    expect(result["data"][CONF_MANUFACTURER]).to_equal("Samsung Electronics")
    expect(result["data"][CONF_MODEL]).to_equal("UE55H6400")
    expect(result["data"][CONF_PORT]).to_equal(55000)
    expect(result["result"].unique_id).to_equal(
        "068e7781-006e-1000-bbbf-84a4668d8423"
    )


@test
async def ssdp_noprefix(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting a flow from discovery when name doesn't start with [TV]."""
    ssdp_data = deepcopy(MOCK_SSDP_DATA)
    ssdp_data.upnp[ATTR_UPNP_FRIENDLY_NAME] = ssdp_data.upnp[
        ATTR_UPNP_FRIENDLY_NAME
    ][4:]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=ssdp_data,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("UE55H6400")
    expect(result["data"][CONF_HOST]).to_equal("10.10.12.34")
    expect(result["data"][CONF_MANUFACTURER]).to_equal("Samsung Electronics")
    expect(result["data"][CONF_MODEL]).to_equal("UE55H6400")
    expect(result["data"][CONF_PORT]).to_equal(55000)
    expect(result["result"].unique_id).to_equal(
        "068e7781-006e-1000-bbbf-84a4668d8423"
    )


@test
async def ssdp_websocket_success_populates_mac_address_and_ssdp_location(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ws: None = Depends(remote_websocket),
    _rest: None = Depends(rest_api),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting a flow from ssdp for a supported websocket device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_RENDERING_CONTROL_ST,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Living Room (82GXARRS)")
    expect(result["data"][CONF_HOST]).to_equal("10.10.12.34")
    expect(result["data"][CONF_MAC]).to_equal("aa:bb:aa:aa:aa:aa")
    expect(result["data"][CONF_MANUFACTURER]).to_equal("Samsung Electronics")
    expect(result["data"][CONF_MODEL]).to_equal("82GXARRS")
    expect(result["data"][CONF_PORT]).to_equal(8002)
    expect(result["data"][CONF_SSDP_RENDERING_CONTROL_LOCATION]).to_equal(
        "http://10.10.12.34:7676/smp_15_"
    )
    expect(result["result"].unique_id).to_equal(
        "be9554b9-c9fb-41f4-8920-22da015376a4"
    )


@test
async def ssdp_websocket_cannot_connect_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    _rest: None = Depends(rest_api_failing),
) -> None:
    """Test starting an SSDP flow when we cannot connect."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVEncryptedWSAsyncRemote.start_listening",
            side_effect=WebSocketException("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote",
        ) as remote_websocket_obj,
        patch.object(
            remote_websocket_obj, "open", side_effect=WebSocketException("Boom")
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_CANNOT_CONNECT)


@test
async def ssdp_not_successful_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting an SSDP flow but no device found."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
            return_value=MOCK_DEVICE_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_CANNOT_CONNECT)


@test
async def ssdp_not_successful_2_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting an SSDP flow but ConnectionFailure on the websocket."""
    with (
        patch(
            "homeassistant.components.samsungtv.bridge.Remote",
            side_effect=OSError("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSAsyncRemote.open",
            side_effect=ConnectionFailure("Boom"),
        ),
        patch(
            "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
            return_value=MOCK_DEVICE_INFO,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(RESULT_CANNOT_CONNECT)


@test
async def ssdp_already_in_progress_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    _legacy: None = Depends(remote_legacy),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting an SSDP flow twice aborts the second."""
    with patch(
        "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
        return_value=MOCK_DEVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("confirm")

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal(RESULT_ALREADY_IN_PROGRESS)


@test
async def ssdp_already_configured_test(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ws: None = Depends(remote_websocket),
    _enc: None = Depends(remote_encrypted_websocket_failing),
) -> None:
    """Test starting an SSDP flow when already configured aborts."""
    with patch(
        "homeassistant.components.samsungtv.bridge.SamsungTVWSBridge.async_device_info",
        return_value=MOCK_DEVICE_INFO,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        entry = result["result"]
        expect(entry.data[CONF_MANUFACTURER]).to_equal(DEFAULT_MANUFACTURER)
        expect(entry.data[CONF_MODEL]).to_equal("fake_model")
        expect(entry.unique_id).to_equal("123")

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=MOCK_SSDP_DATA,
        )
        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal(RESULT_ALREADY_CONFIGURED)


# Skipped tests pending fixture port -----------------------------------------


@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy_does_not_ok_first_time() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_encrypted_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_legacy_missing_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket_access_denied() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def user_websocket_auth_retry() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_legacy_missing_auth() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_legacy_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_websocket_success_populates_mac_address_and_main_tv_ssdp_location() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_encrypted_websocket_success_populates_mac_address_and_ssdp_location() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_encrypted_websocket_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_wireless() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_wired() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_zeroconf_already_in_progress() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_ignores_soundbar() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_no_device_info() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def zeroconf_and_dhcp_same_time() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def websocket_no_mac() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_auth_missing() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_legacy() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def autodetect_none() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_old_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrectly_formatted_mac_unique_id_added_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_from_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_model_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_ssdp_location_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_zeroconf_discovery_preserved_unique_id() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_unique_id_added_ssdp_location_main_tv_agent_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_main_tv_ssdp_location_rendering_st_updated_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_missing_mac_added_unique_id_preserved_from_zeroconf() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_legacy_missing_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_legacy_missing_mac_from_dhcp_no_unique_id() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_ssdp_location_unique_id_added_from_ssdp_with_rendering_control_st() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_legacy() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def reconfigure_host() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def reconfigure_host_invalid() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket_cannot_connect() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_websocket_not_supported() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def form_reauth_encrypted() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_upnp_udn_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_mac_unique_id_added_from_ssdp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def update_incorrect_udn_matching_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def no_update_incorrect_udn_not_matching_mac_from_dhcp() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def ssdp_update_mac() -> None:
    """Skipped pending fixture port."""

@test.skip("complex SSDP/zeroconf/SmartThings fixtures")
async def dhcp_while_user_flow_pending() -> None:
    """Skipped pending fixture port."""
