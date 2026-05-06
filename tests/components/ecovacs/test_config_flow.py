"""Test Ecovacs config flow."""

from collections.abc import Callable
from dataclasses import dataclass, field
import ssl
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientError
from deebot_client.exceptions import InvalidAuthenticationError, MqttError
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
from .const import (
    VALID_ENTRY_DATA_CLOUD,
    VALID_ENTRY_DATA_SELF_HOSTED,
    VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
)

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


def _cannot_connect_error(user_input: dict[str, Any]) -> dict[str, str]:
    field_name = "base"
    if CONF_OVERRIDE_MQTT_URL in user_input:
        field_name = CONF_OVERRIDE_MQTT_URL

    return {field_name: "cannot_connect"}


@test.cases(
    test.case(
        "cloud",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
    ),
    test.case(
        "self_hosted",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED,
    ),
)
async def user_flow(
    test_fn_user_input: _TestFnUserInput,
    entry_data: dict[str, Any],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    authenticate: AsyncMock = Depends(mock_authenticator_authenticate),
    mqtt_client: Mock = Depends(mock_mqtt_client),
) -> None:
    """Test the user config flow."""
    result = await _test_user_flow(hass, test_fn_user_input)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(entry_data[CONF_USERNAME])
    expect(result["data"]).to_equal(entry_data)
    setup_entry.assert_called()
    authenticate.assert_called()
    mqtt_client.verify_config.assert_called()


@test.cases(
    test.case(
        "cloud_rest_cc_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "cloud_rest_cc_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "cloud_rest_cc_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
    test.case(
        "cloud_rest_invalid_auth_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "cloud_rest_invalid_auth_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "cloud_rest_invalid_auth_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
    test.case(
        "cloud_rest_unknown_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "cloud_rest_unknown_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "cloud_rest_unknown_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD),
        entry_data=VALID_ENTRY_DATA_CLOUD,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
    test.case(
        "self_hosted_rest_cc_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "self_hosted_rest_cc_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "self_hosted_rest_cc_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=ClientError,
        reason_rest="cannot_connect",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
    test.case(
        "self_hosted_rest_invalid_auth_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "self_hosted_rest_invalid_auth_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "self_hosted_rest_invalid_auth_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=InvalidAuthenticationError,
        reason_rest="invalid_auth",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
    test.case(
        "self_hosted_rest_unknown_mqtt_cc",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=MqttError,
        errors_mqtt=_cannot_connect_error,
    ),
    test.case(
        "self_hosted_rest_unknown_mqtt_invalid_auth",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=InvalidAuthenticationError,
        errors_mqtt=lambda _: {"base": "invalid_auth"},
    ),
    test.case(
        "self_hosted_rest_unknown_mqtt_unknown",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
        entry_data=VALID_ENTRY_DATA_SELF_HOSTED_WITH_VALIDATE_CERT,
        side_effect_rest=Exception,
        reason_rest="unknown",
        side_effect_mqtt=Exception,
        errors_mqtt=lambda _: {"base": "unknown"},
    ),
)
async def user_flow_raise_error(
    test_fn_user_input: _TestFnUserInput,
    entry_data: dict[str, Any],
    side_effect_rest: type[Exception],
    reason_rest: str,
    side_effect_mqtt: type[Exception],
    errors_mqtt: Callable[[dict[str, Any]], dict[str, str]],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    authenticate: AsyncMock = Depends(mock_authenticator_authenticate),
    mqtt_client: Mock = Depends(mock_mqtt_client),
) -> None:
    """Test handling error on library calls."""
    user_input_auth = test_fn_user_input.auth

    # Authenticator raises error
    authenticate.side_effect = side_effect_rest
    result = await _test_user_flow(hass, test_fn_user_input)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["errors"]).to_equal({"base": reason_rest})
    authenticate.assert_called()
    mqtt_client.verify_config.assert_not_called()
    setup_entry.assert_not_called()

    authenticate.reset_mock(side_effect=True)

    # MQTT raises error
    mqtt_client.verify_config.side_effect = side_effect_mqtt
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input_auth,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("auth")
    expect(result["errors"]).to_equal(errors_mqtt(user_input_auth))
    authenticate.assert_called()
    mqtt_client.verify_config.assert_called()
    setup_entry.assert_not_called()

    authenticate.reset_mock(side_effect=True)
    mqtt_client.verify_config.reset_mock(side_effect=True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=user_input_auth,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(entry_data[CONF_USERNAME])
    expect(result["data"]).to_equal(entry_data)
    setup_entry.assert_called()
    authenticate.assert_called()
    mqtt_client.verify_config.assert_called()


@test
async def user_flow_self_hosted_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    authenticate: AsyncMock = Depends(mock_authenticator_authenticate),
    mqtt_client: Mock = Depends(mock_mqtt_client),
) -> None:
    """Test handling selfhosted errors and custom ssl context."""

    result = await _test_user_flow(
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

    # Check that the schema includes select box to disable ssl verification of mqtt
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
        "cloud", test_fn_user_input=_TestFnUserInput(VALID_ENTRY_DATA_CLOUD)
    ),
    test.case(
        "self_hosted",
        test_fn_user_input=_TestFnUserInput(
            VALID_ENTRY_DATA_SELF_HOSTED, _USER_STEP_SELF_HOSTED
        ),
    ),
)
async def already_exists(
    test_fn_user_input: _TestFnUserInput,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we don't allow duplicated config entries."""
    MockConfigEntry(domain=DOMAIN, data=test_fn_user_input.auth).add_to_hass(hass)

    result = await _test_user_flow(
        hass,
        test_fn_user_input,
    )

    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
