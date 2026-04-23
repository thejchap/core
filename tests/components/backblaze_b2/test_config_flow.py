"""Backblaze B2 config flow tests."""

from unittest.mock import patch

from b2sdk.v2 import exception
from tryke import Depends, expect, fixture, test

from homeassistant.components.backblaze_b2.const import (
    CONF_APPLICATION_KEY,
    CONF_KEY_ID,
    DOMAIN,
)
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigFlowResult,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import USER_INPUT

from tests.common import MockConfigEntry
from tests.components.backblaze_b2._fixtures import (
    BackblazeFixture,
    b2_fixture,
    mock_config_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def _async_start_flow(
    hass: HomeAssistant,
    key_id: str,
    application_key: str,
    user_input: dict[str, str] | None = None,
) -> ConfigFlowResult:
    """Initialize the config flow."""
    if user_input is None:
        user_input = USER_INPUT

    user_input[CONF_KEY_ID] = key_id
    user_input[CONF_APPLICATION_KEY] = application_key
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )


@test
async def basic_flows(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
) -> None:
    """Test basic successful config flows."""
    result = await _async_start_flow(
        hass, b2_fixture.key_id, b2_fixture.application_key
    )
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result.get("title")).to_equal("testBucket")
    expect(result.get("data")).to_equal(USER_INPUT)


@test
async def prefix_normalization(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
) -> None:
    """Test prefix normalization in config flow."""
    user_input = {**USER_INPUT, "prefix": "test-prefix/foo"}
    result = await _async_start_flow(
        hass, b2_fixture.key_id, b2_fixture.application_key, user_input
    )
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]["prefix"]).to_equal("test-prefix/foo/")


@test
async def empty_prefix(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
) -> None:
    """Test empty prefix handling."""
    user_input_empty = {**USER_INPUT, "prefix": ""}
    result = await _async_start_flow(
        hass, b2_fixture.key_id, b2_fixture.application_key, user_input_empty
    )
    expect(result.get("type") is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["data"]["prefix"]).to_equal("")


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
) -> None:
    """Test abort if already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await _async_start_flow(
        hass, b2_fixture.key_id, b2_fixture.application_key
    )
    expect(result.get("type") is FlowResultType.ABORT).to_be(True)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case(
        "invalid_auth",
        "invalid_auth",
        {"key_id": "invalid", "app_key": "invalid"},
        "invalid_credentials",
        "base",
    ),
    test.case(
        "invalid_bucket",
        "invalid_bucket",
        {"bucket": "invalid-bucket-name"},
        "invalid_bucket_name",
        "bucket",
    ),
    test.case(
        "cannot_connect",
        "cannot_connect",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": exception.ConnectionReset,
            "args": ["test"],
        },
        "cannot_connect",
        "base",
    ),
    test.case(
        "restricted_bucket",
        "restricted_bucket",
        {
            "patch": "b2sdk.v2.RawSimulator.get_bucket_by_name",
            "exception": exception.RestrictedBucket,
            "args": ["testBucket"],
        },
        "restricted_bucket",
        "bucket",
    ),
    test.case(
        "missing_account_data",
        "missing_account_data",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": exception.MissingAccountData,
            "args": ["key"],
        },
        "invalid_credentials",
        "base",
    ),
    test.case(
        "invalid_capability",
        "invalid_capability",
        {"mock_capabilities": ["writeFiles", "listFiles", "deleteFiles"]},
        "invalid_capability",
        "base",
    ),
    test.case(
        "no_allowed_info",
        "no_allowed_info",
        {"mock_allowed": None},
        "invalid_capability",
        "base",
    ),
    test.case(
        "no_capabilities",
        "no_capabilities",
        {"mock_allowed": {}},
        "invalid_capability",
        "base",
    ),
    test.case(
        "invalid_prefix",
        "invalid_prefix",
        {"mock_prefix": "test/"},
        "invalid_prefix",
        "prefix",
    ),
    test.case(
        "connection_error",
        "connection_error",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": exception.B2ConnectionError,
            "args": ["Connection error"],
        },
        "cannot_connect",
        "base",
    ),
    test.case(
        "timeout_error",
        "timeout_error",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": exception.B2RequestTimeout,
            "args": ["Request timed out"],
        },
        "cannot_connect",
        "base",
    ),
    test.case(
        "bad_request",
        "bad_request",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": exception.BadRequest,
            "args": ["test", "bad_request"],
        },
        "bad_request",
        "base",
    ),
    test.case(
        "unknown_error",
        "unknown_error",
        {
            "patch": "b2sdk.v2.RawSimulator.authorize_account",
            "exception": RuntimeError,
            "args": ["Unexpected error"],
        },
        "unknown",
        "base",
    ),
)
async def config_flow_errors(
    error_type: str,
    setup: dict,
    expected_error: str,
    expected_field: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
) -> None:
    """Test various config flow error scenarios."""
    if error_type == "invalid_auth":
        result = await _async_start_flow(hass, setup["key_id"], setup["app_key"])
    elif error_type == "invalid_bucket":
        invalid_input = {**USER_INPUT, "bucket": setup["bucket"]}
        result = await _async_start_flow(
            hass, b2_fixture.key_id, b2_fixture.application_key, invalid_input
        )
    elif "patch" in setup:
        with patch(setup["patch"], side_effect=setup["exception"](*setup["args"])):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_capabilities" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value={"capabilities": setup["mock_capabilities"]},
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_allowed" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value=setup["mock_allowed"],
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )
    elif "mock_prefix" in setup:
        with patch(
            "b2sdk.v2.RawSimulator.account_info.get_allowed",
            return_value={
                "capabilities": [
                    "writeFiles",
                    "listFiles",
                    "deleteFiles",
                    "readFiles",
                ],
                "namePrefix": setup["mock_prefix"],
            },
        ):
            result = await _async_start_flow(
                hass, b2_fixture.key_id, b2_fixture.application_key
            )

    expect(result.get("type") is FlowResultType.FORM).to_be(True)
    expect(result.get("errors")).to_equal({expected_field: expected_error})

    if error_type == "restricted_bucket":
        expect(result.get("description_placeholders")).to_equal(
            {
                "brand_name": "Backblaze B2",
                "restricted_bucket_name": "testBucket",
            }
        )
    elif error_type == "invalid_prefix":
        expect(result.get("description_placeholders")).to_equal(
            {
                "brand_name": "Backblaze B2",
                "allowed_prefix": "test/",
            }
        )
    elif error_type == "bad_request":
        expect(result.get("description_placeholders")).to_equal(
            {
                "brand_name": "Backblaze B2",
                "error_message": "test (bad_request)",
            }
        )


@test.cases(
    test.case("reauth_success", "reauth", "success"),
    test.case("reauth_invalid_credentials", "reauth", "invalid_credentials"),
    test.case("reconfigure_success", "reconfigure", "success"),
    test.case(
        "reconfigure_prefix_normalization", "reconfigure", "prefix_normalization"
    ),
    test.case("reconfigure_validation_error", "reconfigure", "validation_error"),
)
async def advanced_flows(
    flow_type: str,
    scenario: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    b2_fixture: BackblazeFixture = Depends(b2_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication and reconfiguration flows."""
    mock_config_entry.add_to_hass(hass)

    if flow_type == "reauth":
        source = SOURCE_REAUTH
        step_name = "reauth_confirm"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": mock_config_entry.entry_id},
        )
        expect(result.get("type") is FlowResultType.FORM).to_be(True)
        expect(result.get("step_id")).to_equal(step_name)

        if scenario == "success":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
            }
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], config
            )
            expect(result.get("type") is FlowResultType.ABORT).to_be(True)
            expect(result.get("reason")).to_equal("reauth_successful")

        else:
            config = {CONF_KEY_ID: "invalid", CONF_APPLICATION_KEY: "invalid"}
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], config
            )
            expect(result.get("type") is FlowResultType.FORM).to_be(True)
            expect(result.get("errors")).to_equal({"base": "invalid_credentials"})

    elif flow_type == "reconfigure":
        source = SOURCE_RECONFIGURE
        step_name = "reconfigure"

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": mock_config_entry.entry_id},
        )
        expect(result.get("type") is FlowResultType.FORM).to_be(True)
        expect(result.get("step_id")).to_equal(step_name)

        if scenario == "success":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
                "bucket": "testBucket",
                "prefix": "new_prefix/",
            }
        elif scenario == "prefix_normalization":
            config = {
                CONF_KEY_ID: b2_fixture.key_id,
                CONF_APPLICATION_KEY: b2_fixture.application_key,
                "bucket": "testBucket",
                "prefix": "no_slash_prefix",
            }
        else:
            config = {
                CONF_KEY_ID: "invalid_key",
                CONF_APPLICATION_KEY: "invalid_app_key",
                "bucket": "invalid_bucket",
                "prefix": "",
            }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )

        if scenario == "validation_error":
            expect(result.get("type") is FlowResultType.FORM).to_be(True)
            expect(result.get("errors")).to_equal({"base": "invalid_credentials"})
        else:
            expect(result.get("type") is FlowResultType.ABORT).to_be(True)
            expect(result.get("reason")).to_equal("reconfigure_successful")
