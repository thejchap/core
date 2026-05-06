"""Tests for the Mitsubishi Comfort config flow."""

from unittest.mock import AsyncMock

from mitsubishi_comfort.exceptions import AuthenticationError, DeviceConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.mitsubishi_comfort.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_cloud_account, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USERNAME = "test@test.com"
MOCK_PASSWORD = "testpass"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_step_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_account: AsyncMock = Depends(mock_cloud_account),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful config flow shows form then creates entry."""
    # First call with no input shows form
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    # Submit credentials creates entry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Mitsubishi Comfort ({MOCK_USERNAME})")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        }
    )
    setup_entry.assert_called_once()


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=AuthenticationError("bad creds"),
        discover_return=None,
        expected_error="invalid_auth",
    ),
    test.case(
        "cannot_connect",
        side_effect=DeviceConnectionError("nope"),
        discover_return=None,
        expected_error="cannot_connect",
    ),
    test.case(
        "unknown_error",
        side_effect=RuntimeError("Unexpected"),
        discover_return=None,
        expected_error="unknown",
    ),
    test.case(
        "no_devices",
        side_effect=None,
        discover_return={},
        expected_error="no_devices",
    ),
)
async def user_step_errors(
    side_effect: Exception | None,
    discover_return: dict | None,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cloud_account: AsyncMock = Depends(mock_cloud_account),
) -> None:
    """Test config flow error handling."""
    if side_effect:
        cloud_account.login.side_effect = side_effect
    elif discover_return is not None:
        cloud_account.discover_devices.return_value = discover_return

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})


@test
async def user_step_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    cloud_account: AsyncMock = Depends(mock_cloud_account),
) -> None:
    """Test that duplicate config is rejected."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: MOCK_USERNAME, CONF_PASSWORD: MOCK_PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
