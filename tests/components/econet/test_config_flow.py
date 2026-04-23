"""Tests for the Econet component."""

from unittest.mock import MagicMock, patch

from pyeconet.api import EcoNetApiInterface
from pyeconet.errors import InvalidCredentialsError, PyeconetError
from tryke import Depends, expect, fixture, test

from homeassistant.components.econet.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.econet._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def bad_credentials(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when provided credentials are rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "pyeconet.EcoNetApiInterface.login",
            side_effect=InvalidCredentialsError(),
        ),
        patch("homeassistant.components.econet.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def generic_error_from_library(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "pyeconet.EcoNetApiInterface.login",
            side_effect=PyeconetError(),
        ),
        patch("homeassistant.components.econet.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def auth_worked(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when provided credentials are accepted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "pyeconet.EcoNetApiInterface.login",
            return_value=EcoNetApiInterface,
        ),
        patch("homeassistant.components.econet.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["data"]).to_equal(
            {
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            }
        )


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test when provided credentials are already configured."""
    config = {
        CONF_EMAIL: "admin@localhost.com",
        CONF_PASSWORD: "password0",
    }
    MockConfigEntry(
        domain=DOMAIN, data=config, unique_id="admin@localhost.com"
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with (
        patch(
            "pyeconet.EcoNetApiInterface.login",
            return_value=EcoNetApiInterface,
        ),
        patch("homeassistant.components.econet.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_EMAIL: "admin@localhost.com",
                CONF_PASSWORD: "password0",
            },
        )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
