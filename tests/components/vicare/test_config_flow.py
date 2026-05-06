"""Test the ViCare config flow."""

from unittest.mock import AsyncMock, patch

from PyViCare.PyViCareUtils import (
    PyViCareInvalidConfigurationError,
    PyViCareInvalidCredentialsError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.vicare.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import MOCK_MAC, MODULE
from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {
    CONF_USERNAME: "foo@bar.com",
    CONF_PASSWORD: "1234",
    CONF_CLIENT_ID: "5678",
}

DHCP_INFO = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="mock_hostname",
    macaddress=MOCK_MAC.lower().replace(":", ""),
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("uses syrupy snapshot")
async def user_create_entry() -> None:
    """Test that the user step works."""


@test
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth flow."""
    new_password = "ABCD"
    new_client_id = "EFGH"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
    )
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        f"{MODULE}.config_flow.login",
        side_effect=PyViCareInvalidConfigurationError(
            {"error": "foo", "error_description": "bar"}
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password, CONF_CLIENT_ID: new_client_id},
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["errors"]).to_equal({"base": "invalid_auth"})

    with patch(
        f"{MODULE}.config_flow.login",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: new_password, CONF_CLIENT_ID: new_client_id},
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("reauth_successful")

        expect(len(hass.config_entries.async_entries())).to_equal(1)
        expect(
            hass.config_entries.async_entries()[0].data[CONF_PASSWORD]
        ).to_equal(new_password)
        expect(
            hass.config_entries.async_entries()[0].data[CONF_CLIENT_ID]
        ).to_equal(new_client_id)
        await hass.async_block_till_done()
    # Reference to ensure imported PyViCareInvalidCredentialsError linked.
    _ = PyViCareInvalidCredentialsError


@test.skip("uses syrupy snapshot")
async def form_dhcp() -> None:
    """Test we can setup from dhcp."""


@test
async def dhcp_single_instance_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that configuring more than one instance is rejected."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=VALID_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_input_single_instance_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that configuring more than one instance is rejected."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="ViCare",
        data=VALID_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
