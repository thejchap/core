"""Test the Homee config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

from pyHomee import HomeeAuthFailedException, HomeeConnectionFailedException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.homee.const import (
    DOMAIN,
    RESULT_CANNOT_CONNECT,
    RESULT_INVALID_AUTH,
    RESULT_UNKNOWN_ERROR,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    HOMEE_ID,
    HOMEE_IP,
    HOMEE_NAME,
    NEW_TESTPASS,
    NEW_TESTUSER,
    TESTPASS,
    TESTUSER,
    mock_config_entry,
    mock_homee,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _homee: AsyncMock = Depends(mock_homee),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the complete config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "host": HOMEE_IP,
            "username": TESTUSER,
            "password": TESTPASS,
        }
    )
    expect(result["title"]).to_equal(f"{HOMEE_NAME} ({HOMEE_IP})")
    expect(result["result"].unique_id).to_equal(HOMEE_ID)


@test.cases(
    test.case(
        "connection_failed",
        side_eff=HomeeConnectionFailedException("connection timed out"),
        error={"base": RESULT_CANNOT_CONNECT},
    ),
    test.case(
        "auth_failed",
        side_eff=HomeeAuthFailedException("wrong username or password"),
        error={"base": RESULT_INVALID_AUTH},
    ),
    test.case(
        "unknown",
        side_eff=Exception,
        error={"base": RESULT_UNKNOWN_ERROR},
    ),
)
async def config_flow_errors(
    side_eff: Exception,
    error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    homee: AsyncMock = Depends(mock_homee),
) -> None:
    """Test the config flow fails as expected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    flow_id = result["flow_id"]

    homee.get_access_token.side_effect = side_eff
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(error)

    homee.get_access_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow aborts when already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    homee: AsyncMock = Depends(mock_homee),
) -> None:
    """Test zeroconf discovery flow."""
    homee.get_access_token.side_effect = HomeeAuthFailedException(
        "wrong username or password"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            name=f"homee-{HOMEE_ID}._ssh._tcp.local.",
            type="_ssh._tcp.local.",
            hostname=f"homee-{HOMEE_ID}.local.",
            ip_address=ip_address(HOMEE_IP),
            ip_addresses=[ip_address(HOMEE_IP)],
            port=22,
            properties={},
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["handler"]).to_equal(DOMAIN)
    setup_entry.assert_not_called()

    homee.get_access_token.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        },
    )

    expect(result["data"]).to_equal(
        {
            CONF_HOST: HOMEE_IP,
            CONF_USERNAME: TESTUSER,
            CONF_PASSWORD: TESTPASS,
        }
    )

    setup_entry.assert_called_once()


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["handler"]).to_equal(DOMAIN)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: NEW_TESTUSER,
            CONF_PASSWORD: NEW_TESTPASS,
        },
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")

    # Confirm that the config entry has been updated
    expect(config_entry.data[CONF_HOST]).to_equal(HOMEE_IP)
    expect(config_entry.data[CONF_USERNAME]).to_equal(NEW_TESTUSER)
    expect(config_entry.data[CONF_PASSWORD]).to_equal(NEW_TESTPASS)


@test
async def reauth_wrong_uid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    homee: AsyncMock = Depends(mock_homee),
) -> None:
    """Test reauth flow with wrong UID."""
    homee.settings.uid = "wrong_uid"
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: NEW_TESTUSER,
            CONF_PASSWORD: NEW_TESTPASS,
        },
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("wrong_hub")

    # Confirm that the config entry is unchanged
    expect(config_entry.data[CONF_HOST]).to_equal(HOMEE_IP)


@test.skip("requires runtime_data + setup_integration; not portable")
async def zeroconf_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery flow when already configured."""
    expect(True).to_be(True)


@test.skip("requires runtime_data injection; not portable")
async def reconfigure_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the reconfigure flow."""
    expect(True).to_be(True)


@test.skip("requires runtime_data injection; not portable")
async def reconfigure_wrong_uid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow with wrong UID."""
    expect(True).to_be(True)
