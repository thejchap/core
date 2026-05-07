"""Tryke ports of the AWS S3 config flow tests."""

from unittest.mock import AsyncMock, patch

from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    ParamValidationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.aws_s3.const import (
    CONF_BUCKET,
    CONF_ENDPOINT_URL,
    CONF_PREFIX,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_client, mock_config_entry
from .const import CONFIG_ENTRY_DATA, USER_INPUT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Module-local fixture-resolution anchor."""


async def _async_start_flow(
    hass: HomeAssistant,
    user_input: dict[str, str] | None = None,
):
    if user_input is None:
        user_input = USER_INPUT

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )


@test.cases(
    test.case(
        "no_prefix",
        user_input=USER_INPUT,
        expected_title="test",
        expected_data=CONFIG_ENTRY_DATA,
    ),
    test.case(
        "with_prefix",
        user_input=USER_INPUT | {CONF_PREFIX: "my-prefix"},
        expected_title="test - my-prefix",
        expected_data=USER_INPUT | {CONF_PREFIX: "my-prefix"},
    ),
    test.case(
        "with_leading_and_trailing_slash",
        user_input=USER_INPUT | {CONF_PREFIX: "/backups/"},
        expected_title="test - backups",
        expected_data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "backups"},
    ),
    test.case(
        "only_slash",
        user_input=USER_INPUT | {CONF_PREFIX: "/"},
        expected_title="test",
        expected_data=CONFIG_ENTRY_DATA,
    ),
    test.case(
        "with_trailing_slash",
        user_input=USER_INPUT | {CONF_PREFIX: "my-prefix/"},
        expected_title="test - my-prefix",
        expected_data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "my-prefix"},
    ),
)
async def flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    *,
    user_input: dict,
    expected_title: str,
    expected_data: dict,
) -> None:
    """Test config flow with and without prefix, including prefix normalization."""
    result = await _async_start_flow(hass, user_input)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(expected_title)
    expect(result["data"]).to_equal(expected_data)


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
    client: AsyncMock = Depends(mock_client),
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

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


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

    client.head_bucket.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


@test
async def abort_if_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the account is already configured."""
    config_entry.add_to_hass(hass)
    result = await _async_start_flow(hass)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid", endpoint_url="@@@"),
    test.case("not_aws", endpoint_url="http://example.com"),
)
async def flow_create_not_aws_endpoint(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
    *,
    endpoint_url: str,
) -> None:
    """Test config flow with a not aws endpoint should raise an error."""
    result = await _async_start_flow(
        hass, USER_INPUT | {CONF_ENDPOINT_URL: endpoint_url}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ENDPOINT_URL: "invalid_endpoint_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


@test
async def abort_if_already_configured_with_same_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we abort if same bucket, endpoint, and prefix are already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "my-prefix"},
    )
    entry.add_to_hass(hass)
    result = await _async_start_flow(hass, USER_INPUT | {CONF_PREFIX: "my-prefix"})
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def abort_if_entry_without_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we abort if an entry without prefix matches bucket and endpoint."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_ENTRY_DATA)
    entry.add_to_hass(hass)
    result = await _async_start_flow(hass, USER_INPUT)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_abort_if_different_prefix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we do not abort when same bucket+endpoint but a different prefix is used."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "prefix-a"},
    )
    entry.add_to_hass(hass)
    result = await _async_start_flow(hass, USER_INPUT | {CONF_PREFIX: "prefix-b"})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_PREFIX]).to_equal("prefix-b")
