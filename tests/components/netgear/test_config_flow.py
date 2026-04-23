"""Tests for the Netgear config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

from pynetgear import DEFAULT_USER
from tryke import Depends, expect, fixture, test

from homeassistant.components.netgear.const import (
    CONF_CONSIDER_HOME,
    DOMAIN,
    MODELS_PORT_5555,
    PORT_80,
    PORT_5555,
)
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_MODEL_NUMBER,
    ATTR_UPNP_PRESENTATION_URL,
    ATTR_UPNP_SERIAL,
    SsdpServiceInfo,
)

from tests.common import MockConfigEntry
from tests.components.netgear._fixtures import ROUTER_INFOS, SERIAL, service
from tests.hass_fixtures import hass as hass_fixture, mock_network

URL = "http://routerlogin.net"
URL_SSL = "https://routerlogin.net"

TITLE = f"{ROUTER_INFOS['ModelName']} - {ROUTER_INFOS['DeviceName']}"
TITLE_INCOMPLETE = ROUTER_INFOS["ModelName"]

HOST = "10.0.0.1"
PORT = 80
SSL = False
USERNAME = "Home_Assistant"
PASSWORD = "password"
SSDP_URL = f"http://{HOST}:{PORT}/rootDesc.xml"
SSDP_URLipv6 = f"http://[::ffff:a00:1]:{PORT}/rootDesc.xml"
SSDP_URL_SLL = f"https://{HOST}:{PORT}/rootDesc.xml"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for all tests."""


@test
async def user(
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(TITLE)
    expect(result["data"].get(CONF_HOST)).to_equal(HOST)
    expect(result["data"].get(CONF_PORT)).to_equal(PORT)
    expect(result["data"].get(CONF_SSL)).to_equal(SSL)
    expect(result["data"].get(CONF_USERNAME)).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)


@test
async def user_connect_error(
    hass: HomeAssistant = Depends(hass_fixture),
    service_: MagicMock = Depends(service),
) -> None:
    """Test user step with connection failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    service_.return_value.get_info = Mock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "info"})

    service_.return_value.login_try_port = Mock(return_value=None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "config"})


@test
async def user_incomplete_info(
    hass: HomeAssistant = Depends(hass_fixture),
    service_: MagicMock = Depends(service),
) -> None:
    """Test user step with incomplete device info."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    router_infos = ROUTER_INFOS.copy()
    router_infos.pop("DeviceName")
    service_.return_value.get_info = Mock(return_value=router_infos)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(TITLE_INCOMPLETE)
    expect(result["data"].get(CONF_HOST)).to_equal(HOST)
    expect(result["data"].get(CONF_PORT)).to_equal(PORT)
    expect(result["data"].get(CONF_SSL)).to_equal(SSL)
    expect(result["data"].get(CONF_USERNAME)).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)


@test
async def abort_if_already_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test we abort if the router is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PASSWORD: PASSWORD},
        unique_id=SERIAL,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ssdp abort when the router is already configured."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PASSWORD: PASSWORD},
        unique_id=SERIAL,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL_SLL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: "RBR20",
                ATTR_UPNP_PRESENTATION_URL: URL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_no_serial(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test ssdp abort when the ssdp info does not include a serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: "RBR20",
                ATTR_UPNP_PRESENTATION_URL: URL,
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial")


@test
async def ssdp_ipv6(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test ssdp abort when using a ipv6 address."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PASSWORD: PASSWORD},
        unique_id=SERIAL,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URLipv6,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: "RBR20",
                ATTR_UPNP_PRESENTATION_URL: URL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_ipv4_address")


@test
async def ssdp(
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test ssdp step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: "RBR20",
                ATTR_UPNP_PRESENTATION_URL: URL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(TITLE)
    expect(result["data"].get(CONF_HOST)).to_equal(HOST)
    expect(result["data"].get(CONF_PORT)).to_equal(PORT_80)
    expect(result["data"].get(CONF_SSL)).to_equal(SSL)
    expect(result["data"].get(CONF_USERNAME)).to_equal(DEFAULT_USER)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)


@test
async def ssdp_port_5555(
    hass: HomeAssistant = Depends(hass_fixture),
    service_: MagicMock = Depends(service),
) -> None:
    """Test ssdp step with port 5555."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL_SLL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: MODELS_PORT_5555[0],
                ATTR_UPNP_PRESENTATION_URL: URL_SSL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    service_.return_value.port = 5555
    service_.return_value.ssl = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(TITLE)
    expect(result["data"].get(CONF_HOST)).to_equal(HOST)
    expect(result["data"].get(CONF_PORT)).to_equal(PORT_5555)
    expect(result["data"].get(CONF_SSL)).to_be(True)
    expect(result["data"].get(CONF_USERNAME)).to_equal(DEFAULT_USER)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test specifying non default settings using options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PASSWORD: PASSWORD},
        unique_id=SERIAL,
        title=TITLE,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_CONSIDER_HOME: 1800,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_CONSIDER_HOME: 1800})
