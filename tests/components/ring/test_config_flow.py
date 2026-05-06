"""Test the Ring config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import ring_doorbell
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ring import DOMAIN
from homeassistant.const import CONF_DEVICE_ID, CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    MOCK_HARDWARE_ID,
    mock_added_config_entry as mock_added_config_entry_fx,
    mock_ring_auth as mock_ring_auth_fx,
    mock_ring_client as mock_ring_client_fx,
    mock_ring_event_listener_class as mock_ring_event_listener_class_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _listener: Mock = Depends(mock_ring_event_listener_class_fx),
) -> None:
    """Wire mock_network and event listener for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    _client: Mock = Depends(mock_ring_client_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch("uuid.uuid4", return_value=MOCK_HARDWARE_ID):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "hello@home-assistant.io", "password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("hello@home-assistant.io")
    expect(result2["data"]).to_equal(
        {
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: "hello@home-assistant.io",
            CONF_TOKEN: {"access_token": "mock-token"},
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        error_type=ring_doorbell.AuthenticationError,
        errors_msg="invalid_auth",
    ),
    test.case("unknown_error", error_type=Exception, errors_msg="unknown"),
)
async def form_error(
    *,
    error_type: type[Exception],
    errors_msg: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ring_auth: Mock = Depends(mock_ring_auth_fx),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mock_ring_auth.async_fetch_token.side_effect = error_type
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "hello@home-assistant.io", "password": "test-password"},
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": errors_msg})


@test
async def form_2fa(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_ring_auth: Mock = Depends(mock_ring_auth_fx),
) -> None:
    """Test form flow for 2fa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    with patch("uuid.uuid4", return_value=MOCK_HARDWARE_ID):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_USERNAME: "foo@bar.com", CONF_PASSWORD: "fake-password"},
        )
    await hass.async_block_till_done()
    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "fake-password", None
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("2fa")
    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "fake-password", "123456"
    )
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("foo@bar.com")
    expect(result3["data"]).to_equal(
        {
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: "foo@bar.com",
            CONF_TOKEN: "new-foobar",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_added_config_entry: MockConfigEntry = Depends(mock_added_config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_ring_auth: Mock = Depends(mock_ring_auth_fx),
) -> None:
    """Test reauth flow."""
    mock_added_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    [result] = flows
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "other_fake_password", None
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("2fa")
    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "other_fake_password", "123456"
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(mock_added_config_entry.data).to_equal(
        {
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: "foo@bar.com",
            CONF_TOKEN: "new-foobar",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        error_type=ring_doorbell.AuthenticationError,
        errors_msg="invalid_auth",
    ),
    test.case("unknown_error", error_type=Exception, errors_msg="unknown"),
)
async def reauth_error(
    *,
    error_type: type[Exception],
    errors_msg: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_added_config_entry: MockConfigEntry = Depends(mock_added_config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_ring_auth: Mock = Depends(mock_ring_auth_fx),
) -> None:
    """Test reauth flow."""
    mock_added_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    [result] = flows
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_ring_auth.async_fetch_token.side_effect = error_type
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "error_fake_password"},
    )
    await hass.async_block_till_done()

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "error_fake_password", None
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": errors_msg})

    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "other_fake_password", None
    )
    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(mock_added_config_entry.data).to_equal(
        {
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: "foo@bar.com",
            CONF_TOKEN: "new-foobar",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def account_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _added: MockConfigEntry = Depends(mock_added_config_entry_fx),
) -> None:
    """Test that user cannot configure the same account twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "foo@bar.com", "password": "test-password"},
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _client: Mock = Depends(mock_ring_client_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test discovery by dhcp."""
    mac_address = "1234567890abcd"
    hostname = "Ring-90abcd"
    ip_address = "127.0.0.1"
    username = "hello@home-assistant.io"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(ip=ip_address, macaddress=mac_address, hostname=hostname),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})
    expect(result["step_id"]).to_equal("user")
    with patch("uuid.uuid4", return_value=MOCK_HARDWARE_ID):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": username, "password": "test-password"},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("hello@home-assistant.io")
    expect(result["data"]).to_equal(
        {
            CONF_DEVICE_ID: MOCK_HARDWARE_ID,
            CONF_USERNAME: username,
            CONF_TOKEN: {"access_token": "mock-token"},
        }
    )

    config_entry = hass.config_entries.async_entry_for_domain_unique_id(
        DOMAIN, username
    )
    expect(bool(config_entry)).to_be(True)

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, mac_address)},
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(ip=ip_address, macaddress=mac_address, hostname=hostname),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
    _client: Mock = Depends(mock_ring_client_fx),
    mock_added_config_entry: MockConfigEntry = Depends(mock_added_config_entry_fx),
) -> None:
    """Test the reconfigure config flow."""
    expect(mock_added_config_entry.data[CONF_DEVICE_ID]).to_equal(MOCK_HARDWARE_ID)

    result = await mock_added_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    with patch("uuid.uuid4", return_value="new-hardware-id"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"password": "test-password"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(mock_added_config_entry.data[CONF_DEVICE_ID]).to_equal("new-hardware-id")


@test.cases(
    test.case(
        "invalid_auth",
        error_type=ring_doorbell.AuthenticationError,
        errors_msg="invalid_auth",
    ),
    test.case("unknown_error", error_type=Exception, errors_msg="unknown"),
)
async def reconfigure_errors(
    *,
    error_type: type[Exception],
    errors_msg: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_added_config_entry: MockConfigEntry = Depends(mock_added_config_entry_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_ring_auth: Mock = Depends(mock_ring_auth_fx),
) -> None:
    """Test errors during the reconfigure config flow."""
    result = await mock_added_config_entry.start_reconfigure_flow(hass)
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_ring_auth.async_fetch_token.side_effect = error_type
    with patch("uuid.uuid4", return_value="new-hardware-id"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "error_fake_password"},
        )
    await hass.async_block_till_done()
    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "error_fake_password", None
    )
    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_PASSWORD: "other_fake_password"},
    )

    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "other_fake_password", None
    )
    expect(result3["type"]).to_be(FlowResultType.FORM)
    expect(result3["step_id"]).to_equal("2fa")

    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "other_fake_password", "123456"
    )

    expect(result4["type"]).to_be(FlowResultType.ABORT)
    expect(result4["reason"]).to_equal("reconfigure_successful")
    expect(mock_added_config_entry.data).to_equal(
        {
            CONF_DEVICE_ID: "new-hardware-id",
            CONF_USERNAME: "foo@bar.com",
            CONF_TOKEN: "new-foobar",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
