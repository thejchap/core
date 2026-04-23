"""Test the AWS S3 config flow."""

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

from tests.common import MockConfigEntry
from tests.components.aws_s3._fixtures import mock_client, mock_config_entry
from tests.hass_fixtures import hass, mock_network

from .const import CONFIG_ENTRY_DATA, USER_INPUT


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def _start_flow(
    hass: HomeAssistant,
    user_input: dict[str, str] | None = None,
) -> FlowResultType:
    """Initialize the config flow."""
    if user_input is None:
        user_input = USER_INPUT

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )


@test.cases(
    test.case("no_prefix", USER_INPUT, "test", CONFIG_ENTRY_DATA),
    test.case(
        "with_prefix",
        USER_INPUT | {CONF_PREFIX: "my-prefix"},
        "test - my-prefix",
        USER_INPUT | {CONF_PREFIX: "my-prefix"},
    ),
    test.case(
        "with_leading_and_trailing_slash",
        USER_INPUT | {CONF_PREFIX: "/backups/"},
        "test - backups",
        CONFIG_ENTRY_DATA | {CONF_PREFIX: "backups"},
    ),
    test.case(
        "only_slash",
        USER_INPUT | {CONF_PREFIX: "/"},
        "test",
        CONFIG_ENTRY_DATA,
    ),
    test.case(
        "with_trailing_slash",
        USER_INPUT | {CONF_PREFIX: "my-prefix/"},
        "test - my-prefix",
        CONFIG_ENTRY_DATA | {CONF_PREFIX: "my-prefix"},
    ),
)
async def flow(
    user_input: dict,
    expected_title: str,
    expected_data: dict,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test config flow with and without prefix, including prefix normalization."""
    result = await _start_flow(hass, user_input)
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(expected_title)
    expect(result["data"]).to_equal(expected_data)


@test.cases(
    test.case(
        "invalid_bucket",
        ParamValidationError(report="Invalid bucket name"),
        {CONF_BUCKET: "invalid_bucket_name"},
    ),
    test.case(
        "invalid_endpoint_url",
        ValueError(),
        {CONF_ENDPOINT_URL: "invalid_endpoint_url"},
    ),
    test.case(
        "cannot_connect",
        EndpointConnectionError(endpoint_url="http://example.com"),
        {CONF_ENDPOINT_URL: "cannot_connect"},
    ),
)
async def flow_create_client_errors(
    exception: Exception,
    errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test config flow errors."""
    with patch(
        "aiobotocore.session.AioSession.create_client",
        side_effect=exception,
    ):
        result = await _start_flow(hass)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


@test
async def flow_head_bucket_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test setup_entry error when calling head_bucket."""
    mock_client.head_bucket.side_effect = ClientError(
        error_response={"Error": {"Code": "InvalidAccessKeyId"}},
        operation_name="head_bucket",
    )
    result = await _start_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({"base": "invalid_credentials"})

    mock_client.head_bucket.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


@test
async def abort_if_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the account is already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await _start_flow(hass)
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_chars", "@@@"),
    test.case("non_aws_endpoint", "http://example.com"),
)
async def flow_create_not_aws_endpoint(
    endpoint_url: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test config flow with a not aws endpoint should raise an error."""
    result = await _start_flow(hass, USER_INPUT | {CONF_ENDPOINT_URL: endpoint_url})

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({CONF_ENDPOINT_URL: "invalid_endpoint_url"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test")
    expect(result["data"]).to_equal(CONFIG_ENTRY_DATA)


@test
async def abort_if_already_configured_with_same_prefix(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we abort if same bucket, endpoint, and prefix are already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "my-prefix"},
    )
    entry.add_to_hass(hass)
    result = await _start_flow(hass, USER_INPUT | {CONF_PREFIX: "my-prefix"})
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def abort_if_entry_without_prefix(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we abort if an entry without prefix matches bucket and endpoint."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_ENTRY_DATA)
    entry.add_to_hass(hass)
    result = await _start_flow(hass, USER_INPUT)
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_abort_if_different_prefix(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_client: AsyncMock = Depends(mock_client),
) -> None:
    """Test we do not abort when same bucket+endpoint but a different prefix is used."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ENTRY_DATA | {CONF_PREFIX: "prefix-a"},
    )
    entry.add_to_hass(hass)
    result = await _start_flow(hass, USER_INPUT | {CONF_PREFIX: "prefix-b"})
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"][CONF_PREFIX]).to_equal("prefix-b")
