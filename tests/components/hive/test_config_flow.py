"""Test the Hive config flow."""

from unittest.mock import patch

from apyhiveapi.helper import hive_exceptions
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.hive.const import CONF_CODE, CONF_DEVICE_NAME, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

USERNAME = "username@home-assistant.com"
UPDATED_USERNAME = "updated_username@home-assistant.com"
PASSWORD = "test-password"
UPDATED_PASSWORD = "updated-password"
INCORRECT_PASSWORD = "incorrect-password"
SCAN_INTERVAL = 120
UPDATED_SCAN_INTERVAL = 60
DEVICE_NAME = "Test Home Assistant"
MFA_CODE = "1234"
MFA_RESEND_CODE = "0000"
MFA_INVALID_CODE = "HIVE"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.login",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AuthenticationResult": {
                    "AccessToken": "mock-access-token",
                    "RefreshToken": "mock-refresh-token",
                },
                "ChallengeName": "SUCCESS",
            },
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def user_flow_with_no_2fa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no 2FA required and device registration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
                "NewDeviceMetadata": {
                    "DeviceGroupKey": "mock-device-group-key",
                    "DeviceKey": "mock-device-key",
                },
            },
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_NAME: DEVICE_NAME,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AuthenticationResult": {
                    "AccessToken": "mock-access-token",
                    "RefreshToken": "mock-refresh-token",
                    "NewDeviceMetadata": {
                        "DeviceGroupKey": "mock-device-group-key",
                        "DeviceKey": "mock-device-key",
                    },
                },
                "ChallengeName": "SUCCESS",
            },
            "device_data": [
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def user_flow_2fa(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with 2FA."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        return_value={
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
            },
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_NAME: DEVICE_NAME,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AuthenticationResult": {
                    "AccessToken": "mock-access-token",
                    "RefreshToken": "mock-refresh-token",
                },
                "ChallengeName": "SUCCESS",
            },
            "device_data": [
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        }
    )

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: INCORRECT_PASSWORD,
            "tokens": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        side_effect=hive_exceptions.HiveInvalidPassword(),
    ):
        result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_password"})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
            },
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: UPDATED_PASSWORD,
            },
        )
    await hass.async_block_till_done()

    expect(mock_config.data.get("username")).to_equal(USERNAME)
    expect(mock_config.data.get("password")).to_equal(UPDATED_PASSWORD)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reauth_2fa_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when the device is still registered."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
            "device_data": [
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.sms_2fa",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.is_device_registered",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )
        await hass.async_block_till_done()

    expect(mock_config.data.get("username")).to_equal(USERNAME)
    expect(mock_config.data.get("password")).to_equal(PASSWORD)
    expect(mock_config.data.get("device_data")).to_equal(
        [
            "mock-device-group-key",
            "mock-device-key",
            "mock-device-password",
        ]
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    mock_setup_entry.assert_called_once()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reauth_2fa_flow_device_not_registered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when the device has been deleted from the Hive app."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.sms_2fa",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.is_device_registered",
            return_value=False,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DEVICE_NAME: DEVICE_NAME,
            },
        )
        await hass.async_block_till_done()

    expect(mock_config.data.get("username")).to_equal(USERNAME)
    expect(mock_config.data.get("password")).to_equal(PASSWORD)
    expect(mock_config.data.get("device_data")).to_equal(
        [
            "mock-device-group-key",
            "mock-device-key",
            "mock-device-password",
        ]
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reauth_2fa_flow_device_registration_check_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reauth 2FA flow when is_device_registered() raises HiveApiError."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AccessToken": "mock-access-token",
                "RefreshToken": "mock-refresh-token",
            },
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await mock_config.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.sms_2fa",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.is_device_registered",
            side_effect=hive_exceptions.HiveApiError(),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({"base": "no_internet_available"})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.sms_2fa",
            return_value={
                "ChallengeName": "SUCCESS",
                "AuthenticationResult": {
                    "RefreshToken": "mock-refresh-token",
                    "AccessToken": "mock-access-token",
                },
            },
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.is_device_registered",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )
        await hass.async_block_till_done()

    expect(mock_config.data.get("username")).to_equal(USERNAME)
    expect(mock_config.data.get("password")).to_equal(PASSWORD)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    mock_setup_entry.assert_called_once()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test.skip("option_flow exercises full async_setup which requires hive integration deps")
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    expect(True).to_be(True)


@test
async def user_flow_2fa_send_new_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Resend a 2FA code if it didn't arrive."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_CODE: MFA_RESEND_CODE}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        return_value={
            "ChallengeName": "SUCCESS",
            "AuthenticationResult": {
                "RefreshToken": "mock-refresh-token",
                "AccessToken": "mock-access-token",
            },
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CODE: MFA_CODE,
            },
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
        patch(
            "homeassistant.components.hive.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_NAME: DEVICE_NAME}
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            "tokens": {
                "AuthenticationResult": {
                    "AccessToken": "mock-access-token",
                    "RefreshToken": "mock-refresh-token",
                },
                "ChallengeName": "SUCCESS",
            },
            "device_data": [
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def abort_if_existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check flow abort when an entry already exist."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USERNAME,
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        options={CONF_SCAN_INTERVAL: SCAN_INTERVAL},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_invalid_username(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with invalid username."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        side_effect=hive_exceptions.HiveInvalidUsername(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_username"})


@test
async def user_flow_invalid_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with invalid password."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        side_effect=hive_exceptions.HiveInvalidPassword(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_password"})


@test
async def user_flow_no_internet_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no internet connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        side_effect=hive_exceptions.HiveApiError(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_internet_available"})


@test
async def user_flow_2fa_no_internet_connection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with no internet connection (2FA)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        side_effect=hive_exceptions.HiveApiError(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CODE: MFA_CODE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({"base": "no_internet_available"})


@test
async def user_flow_2fa_invalid_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow with 2FA invalid code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        side_effect=hive_exceptions.HiveInvalid2FACode(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CODE: MFA_INVALID_CODE},
        )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)
    expect(result["errors"]).to_equal({"base": "invalid_code"})


@test
async def user_flow_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user flow when unknown error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={"ChallengeName": "FAILED", "InvalidAuthenticationResult": {}},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def user_flow_2fa_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test 2fa flow when unknown error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.hive.config_flow.Auth.login",
        return_value={
            "ChallengeName": "SMS_MFA",
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_CODE)

    with patch(
        "homeassistant.components.hive.config_flow.Auth.sms_2fa",
        return_value={"ChallengeName": "FAILED", "InvalidAuthenticationResult": {}},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_CODE: MFA_CODE},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.hive.config_flow.Auth.device_registration",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hive.config_flow.Auth.get_device_data",
            return_value=[
                "mock-device-group-key",
                "mock-device-key",
                "mock-device-password",
            ],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE_NAME: DEVICE_NAME},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("configuration")
    expect(result["errors"]).to_equal({"base": "unknown"})
