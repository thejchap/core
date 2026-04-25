"""Test Ecovacs config flow."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
import ssl
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from deebot_client.mqtt_client import create_mqtt_config
from tryke import Depends, expect, fixture, test

from homeassistant.components.ecovacs.const import (
    CONF_OVERRIDE_MQTT_URL,
    CONF_OVERRIDE_REST_URL,
    CONF_VERIFY_MQTT_CERTIFICATE,
    DOMAIN,
    InstanceMode,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_MODE, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_authenticator_authenticate,
    mock_mqtt_client,
    mock_setup_entry,
)
from .const import VALID_ENTRY_DATA_CLOUD, VALID_ENTRY_DATA_SELF_HOSTED

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

_USER_STEP_SELF_HOSTED = {CONF_MODE: InstanceMode.SELF_HOSTED}


@dataclass
class _TestFnUserInput:
    auth: dict[str, Any]
    user: dict[str, Any] = field(default_factory=dict)


async def _test_user_flow(
    hass: HomeAssistant,
    user_input: _TestFnUserInput,
) -> dict[str, Any]:
    """Test config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(bool(result["errors"])).to_be(False)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input.auth,
    )


async def _test_user_flow_show_advanced_options(
    hass: HomeAssistant,
    user_input: _TestFnUserInput,
) -> dict[str, Any]:
    """Test config flow showing advanced options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input.user,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(bool(result["errors"])).to_be(False)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input.auth,
    )


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test.cases(
    test.case(
        "advanced_cloud",
        test_fn=_test_user_flow_show_advanced_options,
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
    ),
    test.case(
        "advanced_self_hosted",
        test_fn=_test_user_flow_show_advanced_options,
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED,
    ),
    test.case(
        "cloud",
        test_fn=_test_user_flow,
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
    ),
)
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    authenticate: AsyncMock = Depends(mock_authenticator_authenticate),
    mqtt_client: Mock = Depends(mock_mqtt_client),
    *,
    test_fn: Callable[[HomeAssistant, _TestFnUserInput], Awaitable[dict[str, Any]]],
    test_fn_user_input: _TestFnUserInput,
    entry_data: dict[str, Any],
) -> None:
    """Test the user config flow."""
    result = await test_fn(hass, test_fn_user_input)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(entry_data[CONF_USERNAME])
    expect(result["data"]).to_equal(entry_data)
    setup_entry.assert_called()
    authenticate.assert_called()
    mqtt_client.verify_config.assert_called()


@test.skip("complex 27-case cross-product parametrize")
async def user_flow_raise_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling error on library calls."""


@test
async def user_flow_self_hosted_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    authenticate: AsyncMock = Depends(mock_authenticator_authenticate),
    mqtt_client: Mock = Depends(mock_mqtt_client),
) -> None:
    """Test handling selfhosted errors and custom ssl context."""
    result = await _test_user_flow_show_advanced_options(
        hass,
        _TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED
            | {
                CONF_OVERRIDE_REST_URL: "bla://localhost:8000",
                CONF_OVERRIDE_MQTT_URL: "mqtt://",
            },
            _USER_STEP_SELF_HOSTED,
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["errors"]).to_equal(
        {
            CONF_OVERRIDE_REST_URL: "invalid_url_schema_override_rest_url",
            CONF_OVERRIDE_MQTT_URL: "invalid_url",
        }
    )
    authenticate.assert_not_called()
    mqtt_client.verify_config.assert_not_called()
    setup_entry.assert_not_called()

    expect(CONF_VERIFY_MQTT_CERTIFICATE in result["data_schema"].schema).to_be(True)

    data = VALID_ENTRY_DATA_SELF_HOSTED | {CONF_VERIFY_MQTT_CERTIFICATE: False}
    with patch(
        "homeassistant.components.ecovacs.config_flow.create_mqtt_config",
        wraps=create_mqtt_config,
    ) as mock_create_mqtt_config:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=data,
        )
        mock_create_mqtt_config.assert_called_once()
        ssl_context = mock_create_mqtt_config.call_args[1]["ssl_context"]
        expect(isinstance(ssl_context, ssl.SSLContext)).to_be(True)
        expect(ssl_context.verify_mode).to_be(ssl.CERT_NONE)
        expect(ssl_context.check_hostname).to_be(False)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(data[CONF_USERNAME])
    expect(result["data"]).to_equal(data)
    setup_entry.assert_called()
    authenticate.assert_called()
    mqtt_client.verify_config.assert_called()


@test.cases(
    test.case(
        "advanced_cloud",
        test_fn=_test_user_flow_show_advanced_options,
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
    ),
    test.case(
        "advanced_self_hosted",
        test_fn=_test_user_flow_show_advanced_options,
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
    ),
    test.case(
        "cloud",
        test_fn=_test_user_flow,
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
    ),
)
async def already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    test_fn: Callable[[HomeAssistant, _TestFnUserInput], Awaitable[dict[str, Any]]],
    test_fn_user_input: _TestFnUserInput,
) -> None:
    """Test we don't allow duplicated config entries."""
    MockConfigEntry(domain=DOMAIN, data=test_fn_user_input.auth).add_to_hass(hass)

    result = await test_fn(
        hass,
        test_fn_user_input,
    )

    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
