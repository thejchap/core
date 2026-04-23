"""Test the EZVIZ config flow."""

from unittest.mock import AsyncMock

from pyezvizapi.exceptions import (
    EzvizAuthVerificationCode,
    InvalidHost,
    InvalidURL,
    PyEzvizError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.ezviz.const import (
    ATTR_SERIAL,
    ATTR_TYPE_CAMERA,
    ATTR_TYPE_CLOUD,
    CONF_FFMPEG_ARGUMENTS,
    CONF_RFSESSION_ID,
    CONF_SESSION_ID,
    DEFAULT_FFMPEG_ARGUMENTS,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY, SOURCE_USER
from homeassistant.const import (
    CONF_CUSTOMIZE,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_TIMEOUT,
    CONF_TYPE,
    CONF_URL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ezviz import setup_integration
from tests.components.ezviz._fixtures import (
    mock_camera_config_entry,
    mock_config_entry,
    mock_ezviz_client,
    mock_ffmpeg,
    mock_setup_entry,
    mock_test_rtsp_auth,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> None:
    """Trigger the hook executor path."""
    return None


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_SESSION_ID: "fake_token",
            CONF_RFSESSION_ID: "fake_rf_token",
            CONF_URL: "apiieu.ezvizlife.com",
            CONF_TYPE: ATTR_TYPE_CLOUD,
        }
    )
    expect(result["result"].unique_id).to_equal("test-username")

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_custom_url(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test custom url step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: CONF_CUSTOMIZE,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_custom_url")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_SESSION_ID: "fake_token",
            CONF_RFSESSION_ID: "fake_rf_token",
            CONF_URL: "apiieu.ezvizlife.com",
            CONF_TYPE: ATTR_TYPE_CLOUD,
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def async_step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth step."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def step_discovery_abort_if_cloud_account_missing(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
) -> None:
    """Test discovery and confirm step, abort if cloud account was removed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-pass",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("ezviz_cloud_account_missing")


@test
async def step_reauth_abort_if_cloud_account_missing(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
    mock_camera_config_entry: MockConfigEntry = Depends(mock_camera_config_entry),
) -> None:
    """Test reauth and confirm step, abort if cloud account was removed."""
    mock_camera_config_entry.add_to_hass(hass)

    result = await mock_camera_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("ezviz_cloud_account_missing")


@test
async def async_step_integration_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test discovery and confirm step."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-user",
            CONF_PASSWORD: "test-pass",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_PASSWORD: "test-pass",
            CONF_TYPE: ATTR_TYPE_CAMERA,
            CONF_USERNAME: "test-user",
        }
    )
    expect(result["result"].unique_id).to_equal("C666666")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test updating options."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.options[CONF_FFMPEG_ARGUMENTS]).to_equal(
        DEFAULT_FFMPEG_ARGUMENTS
    )
    expect(mock_config_entry.options[CONF_TIMEOUT]).to_equal(DEFAULT_TIMEOUT)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_FFMPEG_ARGUMENTS: "/H.264", CONF_TIMEOUT: 25},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_FFMPEG_ARGUMENTS]).to_equal("/H.264")
    expect(result["data"][CONF_TIMEOUT]).to_equal(25)


@test.cases(
    test.case("invalid_url", exception=InvalidURL, error="invalid_host"),
    test.case("invalid_host", exception=InvalidHost, error="cannot_connect"),
    test.case(
        "mfa_required", exception=EzvizAuthVerificationCode, error="mfa_required"
    ),
    test.case("invalid_auth", exception=PyEzvizError, error="invalid_auth"),
)
async def user_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the user flow with errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_SESSION_ID: "fake_token",
            CONF_RFSESSION_ID: "fake_rf_token",
            CONF_URL: "apiieu.ezvizlife.com",
            CONF_TYPE: ATTR_TYPE_CLOUD,
        }
    )
    expect(result["result"].unique_id).to_equal("test-username")

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_unknown_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
) -> None:
    """Test the user flow with unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test.cases(
    test.case("invalid_url", exception=InvalidURL, error="invalid_host"),
    test.case("invalid_host", exception=InvalidHost, error="cannot_connect"),
    test.case(
        "mfa_required", exception=EzvizAuthVerificationCode, error="mfa_required"
    ),
    test.case("invalid_auth", exception=PyEzvizError, error="invalid_auth"),
)
async def user_custom_url_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the custom url flow with errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: CONF_CUSTOMIZE,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_custom_url")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_custom_url")
    expect(result["errors"]).to_equal({"base": error})

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_SESSION_ID: "fake_token",
            CONF_RFSESSION_ID: "fake_rf_token",
            CONF_URL: "apiieu.ezvizlife.com",
            CONF_TYPE: ATTR_TYPE_CLOUD,
        }
    )
    expect(result["result"].unique_id).to_equal("test-username")

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_custom_url_unknown_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
) -> None:
    """Test the custom url flow with unknown exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
            CONF_URL: CONF_CUSTOMIZE,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_custom_url")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "test-user"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the flow when the account is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured_account")


@test
async def async_step_integration_discovery_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_camera_config_entry: MockConfigEntry = Depends(mock_camera_config_entry),
) -> None:
    """Test discovery aborts when duplicate."""
    mock_config_entry.add_to_hass(hass)
    mock_camera_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("invalid_url", exception=InvalidURL, error="invalid_host"),
    test.case("invalid_host", exception=InvalidHost, error="invalid_host"),
    test.case(
        "mfa_required", exception=EzvizAuthVerificationCode, error="mfa_required"
    ),
    test.case("invalid_auth", exception=PyEzvizError, error="invalid_auth"),
)
async def camera_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the camera flow with errors."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({"base": error})

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("C666666")
    expect(result["data"]).to_equal(
        {
            CONF_TYPE: ATTR_TYPE_CAMERA,
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal("C666666")


@test
async def camera_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    _mock_test_rtsp_auth: AsyncMock = Depends(mock_test_rtsp_auth),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the camera flow with unknown error."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test.cases(
    test.case("invalid_url", exception=InvalidURL, error="invalid_host"),
    test.case("invalid_host", exception=InvalidHost, error="invalid_host"),
    test.case(
        "mfa_required", exception=EzvizAuthVerificationCode, error="mfa_required"
    ),
    test.case("invalid_auth", exception=PyEzvizError, error="invalid_auth"),
)
async def reauth_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth step with errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_unknown_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ffmpeg: None = Depends(mock_ffmpeg),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_ezviz_client: AsyncMock = Depends(mock_ezviz_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth step with unknown exception."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    mock_ezviz_client.login.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")
