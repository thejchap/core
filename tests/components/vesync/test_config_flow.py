"""Test for vesync config flow."""

from unittest.mock import PropertyMock, patch

from pyvesync.utils.errors import VeSyncLoginError
from tryke import Depends, expect, fixture, test

from homeassistant.components.vesync import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    config_entry as config_entry_fx,
    patch_vesync,
    patch_vesync_auth,
    patch_vesync_login,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _login: None = Depends(patch_vesync_login),
    _vesync: None = Depends(patch_vesync),
    _auth: None = Depends(patch_vesync_auth),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def abort_duplicate_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test if we abort because component is already setup under that Account ID."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with (
        patch("pyvesync.vesync.VeSync.login"),
        patch(
            "pyvesync.vesync.VeSync.account_id", new_callable=PropertyMock
        ) as mock_account_id,
    ):
        mock_account_id.return_value = "TESTACCOUNTID"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user@user.com", CONF_PASSWORD: "pass"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def invalid_login_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if we return error for invalid username and password."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "pyvesync.vesync.VeSync.login",
        side_effect=VeSyncLoginError("Mock login failed"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def config_flow_user_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow with user input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch("pyvesync.vesync.VeSync.login"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_USERNAME]).to_equal("user")
    expect(result["data"][CONF_PASSWORD]).to_equal("pass")
    expect(result["result"].unique_id).to_equal("TESTACCOUNTID")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="account_id",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    with (
        patch("pyvesync.vesync.VeSync") as mock_vesync,
        patch(
            "pyvesync.auth.VeSyncAuth._account_id", new_callable=PropertyMock
        ) as mock_account_id,
    ):
        instance = mock_vesync.return_value
        instance.login.return_value = None
        mock_account_id.return_value = "account_id"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_entry.data).to_equal(
        {
            CONF_USERNAME: "new-username",
            CONF_PASSWORD: "new-password",
        }
    )


@test
async def reauth_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test an authorization error reauth flow."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="account_id",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "pyvesync.vesync.VeSync.login",
        side_effect=VeSyncLoginError("Mock login failed"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    with (
        patch("pyvesync.vesync.VeSync") as mock_vesync,
        patch(
            "pyvesync.auth.VeSyncAuth._account_id", new_callable=PropertyMock
        ) as mock_account_id,
    ):
        instance = mock_vesync.return_value
        instance.login.return_value = None
        mock_account_id.return_value = "account_id"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "new-username", CONF_PASSWORD: "new-password"},
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test DHCP discovery flow."""
    service_info = DhcpServiceInfo(
        hostname="Levoit-Purifier",
        ip="1.2.3.4",
        macaddress="aabbccddeeff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=service_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch("pyvesync.vesync.VeSync.login"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal("TESTACCOUNTID")


@test
async def dhcp_discovery_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test DHCP discovery flow with already setup integration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="Levoit-Purifier",
            ip="1.2.3.4",
            macaddress="aabbccddeeff",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
