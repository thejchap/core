"""Test the LG webOS TV config flow."""

from unittest.mock import AsyncMock, Mock

from aiowebostv import WebOsTvPairError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.webostv.const import (
    CONF_SOURCES,
    DEFAULT_NAME,
    DOMAIN,
    LIVE_TV_APP_ID,
)
from homeassistant.config_entries import SOURCE_SSDP
from homeassistant.const import CONF_CLIENT_SECRET, CONF_HOST, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from . import setup_webostv
from ._fixtures import client, mock_setup_entry
from .const import (
    CLIENT_KEY,
    FAKE_UUID,
    HOST,
    MOCK_APPS,
    MOCK_INPUTS,
    TV_MODEL,
    TV_NAME,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


MOCK_USER_CONFIG = {CONF_HOST: HOST}

MOCK_DISCOVERY_INFO = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location=f"http://{HOST}",
    upnp={
        ATTR_UPNP_FRIENDLY_NAME: f"[LG] webOS TV {TV_MODEL}",
        ATTR_UPNP_UDN: f"uuid:{FAKE_UUID}",
    },
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TV_NAME)
    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal(FAKE_UUID)


@test
async def form_no_model_name(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test successful user flow without model name."""
    web_client.tv_info.system = {}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal(FAKE_UUID)


@test.cases(
    test.case(
        "live_tv_in_apps_default",
        apps=MOCK_APPS,
        inputs=MOCK_INPUTS,
    ),
    test.case(
        "live_tv_in_inputs",
        apps={},
        inputs={
            **MOCK_INPUTS,
            "livetv": {"label": "Live TV", "id": "livetv", "appId": LIVE_TV_APP_ID},
        },
    ),
    test.case(
        "live_tv_not_found",
        apps={},
        inputs=MOCK_INPUTS,
    ),
)
async def options_flow_live_tv_in_apps(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
    *,
    apps: dict,
    inputs: dict,
) -> None:
    """Test options config flow Live TV found in apps."""
    web_client.tv_state.apps = apps
    web_client.tv_state.inputs = inputs
    entry = await setup_webostv(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SOURCES: ["Live TV", "Input01", "Input02"]},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_SOURCES]).to_equal(["Live TV", "Input01", "Input02"])


@test.cases(
    test.case("pair_error", side_effect=WebOsTvPairError, error="error_pairing"),
    test.case(
        "connection_reset",
        side_effect=ConnectionResetError,
        error="cannot_connect",
    ),
)
async def options_flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test options config flow errors."""
    entry = await setup_webostv(hass)

    web_client.connect.side_effect = side_effect
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    # recover
    web_client.connect.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=None,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result3 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SOURCES: ["Input01", "Input02"]},
    )

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["data"][CONF_SOURCES]).to_equal(["Input01", "Input02"])


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )

    web_client.connect.side_effect = ConnectionResetError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    # recover
    web_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TV_NAME)


@test
async def form_pairexception(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test pairing exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )

    web_client.connect.side_effect = WebOsTvPairError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "error_pairing"})

    # recover
    web_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TV_NAME)


@test
async def entry_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test entry already configured."""
    await setup_webostv(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def form_ssdp(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test that the ssdp confirmation form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=MOCK_DISCOVERY_INFO
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TV_NAME)
    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal(FAKE_UUID)


@test
async def ssdp_in_progress(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test abort if ssdp paring is already in progress."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=MOCK_USER_CONFIG,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=MOCK_DISCOVERY_INFO
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def form_abort_uuid_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test abort if uuid is already configured, verify host update."""
    entry = await setup_webostv(hass, MOCK_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN][5:])
    expect(entry.unique_id).to_equal(MOCK_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN][5:])
    expect(entry.data[CONF_HOST]).to_equal(HOST)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_config = {CONF_HOST: "new_host"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=user_config,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("pairing")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal("new_host")


@test
async def reauth_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test that the reauthorization is successful."""
    entry = await setup_webostv(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(entry.data[CONF_CLIENT_SECRET]).to_equal(CLIENT_KEY)

    web_client.client_key = "new_key"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_CLIENT_SECRET]).to_equal("new_key")


@test.cases(
    test.case("pair_error", side_effect=WebOsTvPairError, error="error_pairing"),
    test.case(
        "connection_reset",
        side_effect=ConnectionResetError,
        error="cannot_connect",
    ),
)
async def reauth_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test reauthorization errors."""
    entry = await setup_webostv(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    web_client.connect.side_effect = side_effect()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    web_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reconfigure_successful(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test that the reconfigure is successful."""
    entry = await setup_webostv(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "new_host"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_HOST]).to_equal("new_host")


@test.cases(
    test.case("pair_error", side_effect=WebOsTvPairError, error="error_pairing"),
    test.case(
        "connection_reset",
        side_effect=ConnectionResetError,
        error="cannot_connect",
    ),
)
async def reconfigure_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test reconfigure errors."""
    entry = await setup_webostv(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    web_client.connect.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "new_host"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    web_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "new_host"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_wrong_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    web_client: Mock = Depends(client),
) -> None:
    """Test abort if reconfigure host is wrong webOS TV device."""
    entry = await setup_webostv(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    web_client.tv_info.hello = {"deviceUUID": "wrong_uuid"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "new_host"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
