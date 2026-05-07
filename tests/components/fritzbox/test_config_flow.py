"""Test the fritzbox config flow."""

import dataclasses
from unittest import mock
from unittest.mock import Mock
from urllib.parse import urlparse

from pyfritzhome import LoginError
from requests.exceptions import HTTPError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fritzbox.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from ._fixtures import fritz
from .const import CONF_FAKE_NAME, MOCK_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


MOCK_USER_DATA = MOCK_CONFIG[DOMAIN][CONF_DEVICES][0]
MOCK_SSDP_DATA = {
    "ip4_valid": SsdpServiceInfo(
        ssdp_usn="mock_usn",
        ssdp_st="mock_st",
        ssdp_location="https://10.0.0.1:12345/test",
        upnp={
            ATTR_UPNP_FRIENDLY_NAME: CONF_FAKE_NAME,
            ATTR_UPNP_UDN: "uuid:only-a-test",
        },
    ),
    "ip6_valid": SsdpServiceInfo(
        ssdp_usn="mock_usn",
        ssdp_st="mock_st",
        ssdp_location="https://[1234::1]:12345/test",
        upnp={
            ATTR_UPNP_FRIENDLY_NAME: CONF_FAKE_NAME,
            ATTR_UPNP_UDN: "uuid:only-a-test",
        },
    ),
    "ip6_invalid": SsdpServiceInfo(
        ssdp_usn="mock_usn",
        ssdp_st="mock_st",
        ssdp_location="https://[fe80::1%1]:12345/test",
        upnp={
            ATTR_UPNP_FRIENDLY_NAME: CONF_FAKE_NAME,
            ATTR_UPNP_UDN: "uuid:only-a-test",
        },
    ),
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.0.0.1")
    expect(result["data"][CONF_HOST]).to_equal("10.0.0.1")
    expect(result["data"][CONF_PASSWORD]).to_equal("fake_pass")
    expect(result["data"][CONF_USERNAME]).to_equal("fake_user")
    expect(bool(result["result"].unique_id)).to_be(False)


@test
async def user_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow by user with authentication failure."""
    fritz_mock().login.side_effect = [LoginError("Boom"), mock.DEFAULT]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def user_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow by user but no connection found."""
    fritz_mock().login.side_effect = OSError("Boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow by user when already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(bool(result["result"].unique_id)).to_be(False)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a reauthentication flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config.data[CONF_USERNAME]).to_equal("other_fake_user")
    expect(mock_config.data[CONF_PASSWORD]).to_equal("other_fake_password")


@test
async def reauth_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a reauthentication flow with authentication failure."""
    fritz_mock().login.side_effect = LoginError("Boom")

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def reauth_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a reauthentication flow but no connection found."""
    fritz_mock().login.side_effect = OSError("Boom")

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def reconfigure_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a reconfigure flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)

    expect(mock_config.data[CONF_HOST]).to_equal("10.0.0.1")
    expect(mock_config.data[CONF_USERNAME]).to_equal("fake_user")
    expect(mock_config.data[CONF_PASSWORD]).to_equal("fake_pass")

    result = await mock_config.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "new_host"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config.data[CONF_HOST]).to_equal("new_host")
    expect(mock_config.data[CONF_USERNAME]).to_equal("fake_user")
    expect(mock_config.data[CONF_PASSWORD]).to_equal("fake_pass")


@test
async def reconfigure_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a reconfigure flow with failure."""
    fritz_mock().login.side_effect = [OSError("Boom"), None]

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "new_host"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]["base"]).to_equal("no_devices_found")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "new_host"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config.data[CONF_HOST]).to_equal("new_host")


@test.cases(
    test.case(
        "ip4_valid",
        test_data=MOCK_SSDP_DATA["ip4_valid"],
        expected_result=FlowResultType.FORM,
    ),
    test.case(
        "ip6_valid",
        test_data=MOCK_SSDP_DATA["ip6_valid"],
        expected_result=FlowResultType.FORM,
    ),
    test.case(
        "ip6_invalid",
        test_data=MOCK_SSDP_DATA["ip6_invalid"],
        expected_result=FlowResultType.ABORT,
    ),
)
async def ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
    *,
    test_data: SsdpServiceInfo,
    expected_result: FlowResultType,
) -> None:
    """Test starting a flow from discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=test_data
    )
    expect(result["type"]).to_equal(expected_result)

    if expected_result is FlowResultType.ABORT:
        return

    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(CONF_FAKE_NAME)
    expect(result["data"][CONF_HOST]).to_equal(
        urlparse(test_data.ssdp_location).hostname
    )
    expect(result["data"][CONF_PASSWORD]).to_equal("fake_pass")
    expect(result["data"][CONF_USERNAME]).to_equal("fake_user")
    expect(result["result"].unique_id).to_equal("only-a-test")


@test
async def ssdp_no_friendly_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery without friendly name."""
    MOCK_NO_NAME = dataclasses.replace(MOCK_SSDP_DATA["ip4_valid"])
    MOCK_NO_NAME.upnp = MOCK_NO_NAME.upnp.copy()
    del MOCK_NO_NAME.upnp[ATTR_UPNP_FRIENDLY_NAME]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_NO_NAME
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.0.0.1")
    expect(result["data"][CONF_HOST]).to_equal("10.0.0.1")
    expect(result["data"][CONF_PASSWORD]).to_equal("fake_pass")
    expect(result["data"][CONF_USERNAME]).to_equal("fake_user")
    expect(result["result"].unique_id).to_equal("only-a-test")


@test
async def ssdp_auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery with authentication failure."""
    fritz_mock().login.side_effect = LoginError("Boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def ssdp_not_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery but no device found."""
    fritz_mock().login.side_effect = OSError("Boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def ssdp_not_supported(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery with unsupported device."""
    fritz_mock().get_device_elements.side_effect = HTTPError("Boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_supported")


@test
async def ssdp_already_in_progress_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def ssdp_already_in_progress_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    MOCK_NO_UNIQUE_ID = dataclasses.replace(MOCK_SSDP_DATA["ip4_valid"])
    MOCK_NO_UNIQUE_ID.upnp = MOCK_NO_UNIQUE_ID.upnp.copy()
    del MOCK_NO_UNIQUE_ID.upnp[ATTR_UPNP_UDN]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_NO_UNIQUE_ID
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def ssdp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fritz_mock: Mock = Depends(fritz),
) -> None:
    """Test starting a flow from discovery when already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(bool(result["result"].unique_id)).to_be(False)

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA["ip4_valid"]
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    expect(result["result"].unique_id).to_equal("only-a-test")
