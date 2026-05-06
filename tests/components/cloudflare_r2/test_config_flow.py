"""Test the Cloudflare R2 config flow."""

from unittest.mock import AsyncMock, patch

from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ParamValidationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.cloudflare_r2.const import (
    CONF_BUCKET,
    CONF_ENDPOINT_URL,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_client, mock_config_entry as mock_config_entry_fixture
from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _client: AsyncMock = Depends(mock_client),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


async def _async_start_flow(
    hass: HomeAssistant,
    user_input: dict[str, str] | None = None,
) -> dict:
    """Initialize the config flow."""
    if user_input is None:
        user_input = USER_INPUT

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )


@test
async def flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow."""
    result = await _async_start_flow(hass)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test.cases(
    test.case(
        "param_validation_error",
        exception=ParamValidationError(report="Invalid bucket name"),
        errors={CONF_BUCKET: "invalid_bucket_name"},
    ),
    test.case(
        "value_error",
        exception=ValueError(),
        errors={CONF_ENDPOINT_URL: "invalid_endpoint_url"},
    ),
    test.case(
        "endpoint_connection_error",
        exception=EndpointConnectionError(endpoint_url="http://example.com"),
        errors={CONF_ENDPOINT_URL: "cannot_connect"},
    ),
)
async def flow_create_client_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    exception: Exception,
    errors: dict[str, str],
) -> None:
    """Test config flow errors."""
    with patch(
        "aiobotocore.session.AioSession.create_client",
        side_effect=exception,
    ):
        result = await _async_start_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(errors)

    # Fix and finish the test.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test
async def flow_head_bucket_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test setup_entry error when calling head_bucket."""
    client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "InvalidAccessKeyId"}},
        operation_name="head_bucket",
    )
    result = await _async_start_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_credentials"})

    # Fix and finish the test.
    client.head_bucket.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)


@test
async def abort_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test we abort if the account is already configured."""
    config_entry.add_to_hass(hass)
    result = await _async_start_flow(hass)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_create_not_r2_endpoint(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow with a not R2 endpoint should raise an error."""
    result = await _async_start_flow(
        hass, USER_INPUT | {CONF_ENDPOINT_URL: "http://example.com"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ENDPOINT_URL: "invalid_endpoint_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(USER_INPUT)
