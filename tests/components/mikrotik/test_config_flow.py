"""Test Mikrotik setup process."""

from contextlib import contextmanager
from unittest.mock import patch

import librouteros
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mikrotik.const import (
    CONF_ARP_PING,
    CONF_DETECTION_TIME,
    CONF_FORCE_DHCP,
    DOMAIN,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DEMO_USER_INPUT = {
    CONF_HOST: "0.0.0.0",
    CONF_USERNAME: "username",
    CONF_PASSWORD: "password",
    CONF_PORT: 8278,
    CONF_VERIFY_SSL: False,
}

DEMO_CONFIG_ENTRY = {
    CONF_HOST: "0.0.0.0",
    CONF_USERNAME: "username",
    CONF_PASSWORD: "password",
    CONF_PORT: 8278,
    CONF_VERIFY_SSL: False,
    CONF_FORCE_DHCP: False,
    CONF_ARP_PING: False,
    CONF_DETECTION_TIME: 30,
}


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@contextmanager
def _mock_api():
    """Mock a working librouteros.connect."""
    with patch("librouteros.connect"):
        yield


@contextmanager
def _mock_auth_error():
    """Mock librouteros.connect raising an auth error."""
    with patch(
        "librouteros.connect",
        side_effect=librouteros.exceptions.TrapError("invalid user name or password"),
    ):
        yield


@contextmanager
def _mock_conn_error():
    """Mock librouteros.connect raising a connection error."""
    with patch(
        "librouteros.connect", side_effect=librouteros.exceptions.ConnectionClosed
    ):
        yield


@test
async def flow_works(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow."""
    with _mock_api():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=DEMO_USER_INPUT
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Mikrotik (0.0.0.0)")
        expect(result["data"][CONF_HOST]).to_equal("0.0.0.0")
        expect(result["data"][CONF_USERNAME]).to_equal("username")
        expect(result["data"][CONF_PASSWORD]).to_equal("password")
        expect(result["data"][CONF_PORT]).to_equal(8278)


@test
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test updating options."""
    with _mock_api():
        entry = MockConfigEntry(domain=DOMAIN, data=DEMO_CONFIG_ENTRY)
        entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("device_tracker")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_DETECTION_TIME: 30,
                CONF_ARP_PING: True,
                CONF_FORCE_DHCP: False,
            },
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(
            {
                CONF_DETECTION_TIME: 30,
                CONF_ARP_PING: True,
                CONF_FORCE_DHCP: False,
            }
        )


@test
async def host_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test host already configured."""
    with _mock_auth_error():
        entry = MockConfigEntry(domain=DOMAIN, data=DEMO_CONFIG_ENTRY)
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=DEMO_USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test error when connection is unsuccessful."""
    with _mock_conn_error():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=DEMO_USER_INPUT
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def wrong_credentials(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test error when credentials are wrong."""
    with _mock_auth_error():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=DEMO_USER_INPUT
        )

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(
            {
                CONF_USERNAME: "invalid_auth",
                CONF_PASSWORD: "invalid_auth",
            }
        )


@test
async def reauth_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can reauth."""
    with _mock_api():
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=DEMO_USER_INPUT,
        )
        entry.add_to_hass(hass)

        result = await entry.start_reauth_flow(hass)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["description_placeholders"]).to_equal(
            {
                CONF_NAME: "Mock Title",
                CONF_USERNAME: "username",
            }
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauth_failed(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth fails due to wrong password."""
    with _mock_auth_error():
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=DEMO_USER_INPUT,
        )
        entry.add_to_hass(hass)

        result = await entry.start_reauth_flow(hass)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-wrong-password"},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({CONF_PASSWORD: "invalid_auth"})


@test
async def reauth_failed_conn_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test reauth failed due to connection error."""
    with _mock_conn_error():
        entry = MockConfigEntry(
            domain=DOMAIN,
            data=DEMO_USER_INPUT,
        )
        entry.add_to_hass(hass)

        result = await entry.start_reauth_flow(hass)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-wrong-password"},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})
