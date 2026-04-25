"""Tests for the iCloud config flow."""

from unittest.mock import MagicMock, patch

from pyicloud.exceptions import PyiCloudFailedLoginException
from tryke import Depends, expect, fixture, test

from homeassistant.components.icloud.config_flow import (
    CONF_TRUSTED_DEVICE,
    CONF_VERIFICATION_CODE,
)
from homeassistant.components.icloud.const import (
    CONF_GPS_ACCURACY_THRESHOLD,
    CONF_MAX_INTERVAL,
    CONF_WITH_FAMILY,
    DEFAULT_GPS_ACCURACY_THRESHOLD,
    DEFAULT_MAX_INTERVAL,
    DEFAULT_WITH_FAMILY,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    icloud_bypass_setup,
    service,
    service_2fa,
    service_authenticated,
    service_authenticated_no_device,
    service_send_verification_code_failed,
    service_validate_2fa_code_failed,
    service_validate_verification_code_failed,
)
from .const import (
    MOCK_CONFIG,
    PASSWORD,
    PASSWORD_2,
    USERNAME,
    WITH_FAMILY,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bypass: None = Depends(icloud_bypass_setup),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=None
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_TRUSTED_DEVICE)


@test
async def user_with_cookie(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_authenticated),
) -> None:
    """Test user config with presence of a cookie."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
            CONF_WITH_FAMILY: WITH_FAMILY,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(USERNAME)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_WITH_FAMILY]).to_equal(WITH_FAMILY)
    expect(result["data"][CONF_MAX_INTERVAL]).to_equal(DEFAULT_MAX_INTERVAL)
    expect(result["data"][CONF_GPS_ACCURACY_THRESHOLD]).to_equal(
        DEFAULT_GPS_ACCURACY_THRESHOLD
    )


@test
async def login_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test when we have errors during login."""
    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService",
        side_effect=PyiCloudFailedLoginException(msg="Invalid login"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test
async def no_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_authenticated_no_device),
) -> None:
    """Test when we have no devices."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_device")


@test
async def trusted_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test trusted_device step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_TRUSTED_DEVICE)


@test
async def trusted_device_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test trusted_device step success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TRUSTED_DEVICE: 0}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_VERIFICATION_CODE)


@test
async def send_verification_code_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_send_verification_code_failed),
) -> None:
    """Test when we have errors during send_verification_code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TRUSTED_DEVICE: 0}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_TRUSTED_DEVICE)
    expect(result["errors"]).to_equal({CONF_TRUSTED_DEVICE: "send_verification_code"})


@test
async def verification_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service),
) -> None:
    """Test verification_code step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TRUSTED_DEVICE: 0}
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_VERIFICATION_CODE)


@test
async def verification_code_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_mock: MagicMock = Depends(service),
) -> None:
    """Test verification_code step success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TRUSTED_DEVICE: 0}
    )
    service_mock.return_value.requires_2sa = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_VERIFICATION_CODE: "0"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(USERNAME)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_WITH_FAMILY]).to_equal(DEFAULT_WITH_FAMILY)
    expect(result["data"][CONF_MAX_INTERVAL]).to_equal(DEFAULT_MAX_INTERVAL)
    expect(result["data"][CONF_GPS_ACCURACY_THRESHOLD]).to_equal(
        DEFAULT_GPS_ACCURACY_THRESHOLD
    )


@test
async def validate_verification_code_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_validate_verification_code_failed),
) -> None:
    """Test when we have errors during validate_verification_code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TRUSTED_DEVICE: 0}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_VERIFICATION_CODE: "0"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_TRUSTED_DEVICE)
    expect(result["errors"]).to_equal({"base": "validate_verification_code"})


@test
async def f2a_code_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    service_mock: MagicMock = Depends(service_2fa),
) -> None:
    """Test 2fa step success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    service_mock.return_value.requires_2fa = False
    service_mock.return_value.requires_2sa = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_VERIFICATION_CODE: "0"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(USERNAME)
    expect(result["title"]).to_equal(USERNAME)
    expect(result["data"][CONF_USERNAME]).to_equal(USERNAME)
    expect(result["data"][CONF_PASSWORD]).to_equal(PASSWORD)
    expect(result["data"][CONF_WITH_FAMILY]).to_equal(DEFAULT_WITH_FAMILY)
    expect(result["data"][CONF_MAX_INTERVAL]).to_equal(DEFAULT_MAX_INTERVAL)
    expect(result["data"][CONF_GPS_ACCURACY_THRESHOLD]).to_equal(
        DEFAULT_GPS_ACCURACY_THRESHOLD
    )


@test
async def validate_2fa_code_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_validate_2fa_code_failed),
) -> None:
    """Test when we have errors during validate_verification_code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_VERIFICATION_CODE: "0"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(CONF_VERIFICATION_CODE)
    expect(result["errors"]).to_equal({"base": "validate_verification_code"})


@test
async def password_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _service: MagicMock = Depends(service_authenticated),
) -> None:
    """Test that password reauthentication works successfully."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, entry_id="test", unique_id=USERNAME
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD_2}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal(PASSWORD_2)


@test
async def password_update_wrong_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that during password reauthentication wrong password returns correct error."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, entry_id="test", unique_id=USERNAME
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.icloud.config_flow.PyiCloudService",
        side_effect=PyiCloudFailedLoginException(msg="Invalid login"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: PASSWORD_2}
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})
