"""Tests for the Tuya config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.tuya.const import CONF_USER_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_setup_entry,
    mock_tuya_login_control,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test.skip("uses syrupy snapshot")
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _login: MagicMock = Depends(mock_tuya_login_control),
) -> None:
    """Test the full happy path user flow from start to finish."""


@test
async def user_flow_failed_qr_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_tuya_login_control),
) -> None:
    """Test an error occurring while retrieving the QR code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    # Something went wrong getting the QR code (like an invalid user code).
    login.qr_code.return_value["success"] = False

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "login_error"})

    # This time it worked out.
    login.qr_code.return_value["success"] = True

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )
    expect(result3.get("step_id")).to_equal("scan")

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_failed_scan(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_tuya_login_control),
) -> None:
    """Test an error occurring while verifying login."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("scan")

    # Access has been denied, or the code hasn't been scanned yet.
    good_values = login.login_result.return_value
    login.login_result.return_value = (
        False,
        {"msg": "oops", "code": 42},
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result3.get("type")).to_be(FlowResultType.FORM)
    expect(result3.get("errors")).to_equal({"base": "login_error"})

    # This time it worked out.
    login.login_result.return_value = good_values

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result4.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test.skip("uses syrupy snapshot")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _login: MagicMock = Depends(mock_tuya_login_control),
) -> None:
    """Test the reauthentication configuration flow."""


@test
async def reauth_flow_failed_qr_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    login: MagicMock = Depends(mock_tuya_login_control),
    config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test an error occurring while retrieving the QR code."""
    config_entry.add_to_hass(hass)

    # Something went wrong getting the QR code (like an invalid user code).
    login.qr_code.return_value["success"] = False

    result = await config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_user_code")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("errors")).to_equal({"base": "login_error"})

    # This time it worked out.
    login.qr_code.return_value["success"] = True

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USER_CODE: "12345"},
    )
    expect(result3.get("step_id")).to_equal("scan")

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result3.get("type")).to_be(FlowResultType.ABORT)
    expect(result3.get("reason")).to_equal("reauth_successful")
