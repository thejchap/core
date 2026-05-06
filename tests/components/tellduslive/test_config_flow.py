"""Tests for the TelldusLive config flow."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import data_entry_flow
from homeassistant.components.tellduslive import (
    APPLICATION_NAME,
    DOMAIN,
    KEY_SCAN_INTERVAL,
    SCAN_INTERVAL,
    config_flow,
)
from homeassistant.config_entries import SOURCE_DISCOVERY
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_tellduslive,
    mock_tellduslive_no_local_api,
    mock_tellduslive_unauthorized,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def init_config_flow(
    hass: HomeAssistant, side_effect: type[Exception] | None = None
) -> config_flow.FlowHandler:
    """Init a configuration flow."""
    flow = config_flow.FlowHandler()
    flow.hass = hass
    if side_effect:
        flow._get_auth_url = Mock(side_effect=side_effect)
    return flow


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if TelldusLive is already setup."""
    flow = init_config_flow(hass)

    with patch.object(hass.config_entries, "async_entries", return_value=[{}]):
        result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_setup")

    with patch.object(hass.config_entries, "async_entries", return_value=[{}]):
        result = await flow.async_step_import(None)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_setup")


@test
async def full_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test registering an implementation and finishing flow works."""
    flow = init_config_flow(hass)
    flow.context = {"source": SOURCE_DISCOVERY}
    result = await flow.async_step_discovery(["localhost", "tellstick"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(len(flow._hosts)).to_equal(2)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await flow.async_step_user({"host": "localhost"})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["description_placeholders"]).to_equal(
        {
            "auth_url": "https://example.com",
            "app_name": APPLICATION_NAME,
        }
    )

    result = await flow.async_step_auth("")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("localhost")
    expect(result["data"]["host"]).to_equal("localhost")
    expect(result["data"]["scan_interval"]).to_equal(60)
    expect(result["data"]["session"]).to_equal({"token": "token", "host": "localhost"})


@test
async def step_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that we trigger auth when configuring from import."""
    flow = init_config_flow(hass)

    result = await flow.async_step_import({CONF_HOST: DOMAIN, KEY_SCAN_INTERVAL: 0})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")


@test
async def step_import_add_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that we add host and trigger user when configuring from import."""
    flow = init_config_flow(hass)

    result = await flow.async_step_import(
        {CONF_HOST: "localhost", KEY_SCAN_INTERVAL: 0}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_import_no_config_file(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that we trigger user with no config_file configuring from import."""
    flow = init_config_flow(hass)

    result = await flow.async_step_import(
        {CONF_HOST: "localhost", KEY_SCAN_INTERVAL: 0}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_import_load_json_matching_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that we add host and trigger user when configuring from import."""
    flow = init_config_flow(hass)

    with (
        patch(
            "homeassistant.components.tellduslive.config_flow.load_json_object",
            return_value={"tellduslive": {}},
        ),
        patch("os.path.isfile"),
    ):
        result = await flow.async_step_import(
            {CONF_HOST: "Cloud API", KEY_SCAN_INTERVAL: 0}
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_import_load_json(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that we create entry when configuring from import."""
    flow = init_config_flow(hass)

    with (
        patch(
            "homeassistant.components.tellduslive.config_flow.load_json_object",
            return_value={"localhost": {}},
        ),
        patch("os.path.isfile"),
    ):
        result = await flow.async_step_import(
            {CONF_HOST: "localhost", KEY_SCAN_INTERVAL: SCAN_INTERVAL}
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("localhost")
    expect(result["data"]["host"]).to_equal("localhost")
    expect(result["data"]["scan_interval"]).to_equal(60)
    expect(result["data"]["session"]).to_equal({})


@test
async def step_disco_no_local_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive_no_local_api),
) -> None:
    """Test that we trigger when configuring from discovery, not supporting local api."""
    flow = init_config_flow(hass)
    flow.context = {"source": SOURCE_DISCOVERY}

    result = await flow.async_step_discovery(["localhost", "tellstick"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(len(flow._hosts)).to_equal(1)


@test
async def step_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test that create cloud entity from auth."""
    flow = init_config_flow(hass)

    await flow.async_step_auth()
    result = await flow.async_step_auth(["localhost", "tellstick"])
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Cloud API")
    expect(result["data"]["host"]).to_equal("Cloud API")
    expect(result["data"]["scan_interval"]).to_equal(60)
    expect(result["data"]["session"]).to_equal(
        {
            "token": "token",
            "token_secret": "token_secret",
        }
    )


@test
async def wrong_auth_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive_unauthorized),
) -> None:
    """Test wrong auth."""
    flow = init_config_flow(hass)

    await flow.async_step_auth()
    result = await flow.async_step_auth("")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def not_pick_host_if_only_one(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test not picking host if we have just one."""
    flow = init_config_flow(hass)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")


@test
async def abort_if_timeout_generating_auth_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test abort if generating authorize url timeout."""
    flow = init_config_flow(hass, side_effect=TimeoutError)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("authorize_url_timeout")


@test
async def abort_no_auth_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test abort if generating authorize url returns none."""
    flow = init_config_flow(hass)
    flow._get_auth_url = Mock(return_value=False)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown_authorize_url_generation")


@test
async def abort_if_exception_generating_auth_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test we abort if generating authorize url blows up."""
    flow = init_config_flow(hass, side_effect=ValueError)

    result = await flow.async_step_user()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown_authorize_url_generation")


@test
async def discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _tellduslive: tuple = Depends(mock_tellduslive),
) -> None:
    """Test abort if already configured fires from discovery."""
    MockConfigEntry(domain="tellduslive", data={"host": "some-host"}).add_to_hass(hass)
    flow = init_config_flow(hass)
    flow.context = {"source": SOURCE_DISCOVERY}

    raised = False
    try:
        await flow.async_step_discovery(["some-host", ""])
    except data_entry_flow.AbortFlow:
        raised = True
    expect(raised).to_be(True)
