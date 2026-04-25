"""Tests for the Fumis config flow."""

from unittest.mock import MagicMock

from fumis import FumisAuthenticationError, FumisConnectionError, FumisStoveOfflineError
from tryke import Depends, expect, fixture, test

from homeassistant.components.fumis.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_MAC, CONF_PIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_fumis, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _fumis: MagicMock = Depends(mock_fumis),
) -> None:
    """Test the full user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_MAC: "AABBCCDDEEFF",
            CONF_PIN: "1234",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Clou Duo")
    expect(result["data"]).to_equal(
        {
            CONF_MAC: "AABBCCDDEEFF",
            CONF_PIN: "1234",
        }
    )
    expect(result["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test.cases(
    test.case(
        "auth",
        side_effect=FumisAuthenticationError,
        expected_error={CONF_PIN: "invalid_auth"},
    ),
    test.case(
        "offline",
        side_effect=FumisStoveOfflineError,
        expected_error={"base": "device_offline"},
    ),
    test.case(
        "connection",
        side_effect=FumisConnectionError,
        expected_error={"base": "cannot_connect"},
    ),
    test.case(
        "unknown",
        side_effect=Exception,
        expected_error={"base": "unknown"},
    ),
)
async def user_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    fumis: MagicMock = Depends(mock_fumis),
    *,
    side_effect: type[Exception],
    expected_error: dict[str, str],
) -> None:
    """Test the user flow with errors."""
    fumis.update_info.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_MAC: "AABBCCDDEEFF",
            CONF_PIN: "1234",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(expected_error)

    fumis.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_MAC: "AABBCCDDEEFF",
            CONF_PIN: "1234",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("colon_lower", mac_input="aa:bb:cc:dd:ee:ff"),
    test.case("colon_upper", mac_input="AA:BB:CC:DD:EE:FF"),
    test.case("dash_lower", mac_input="aa-bb-cc-dd-ee-ff"),
    test.case("plain_lower", mac_input="aabbccddeeff"),
)
async def user_flow_mac_normalization(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _fumis: MagicMock = Depends(mock_fumis),
    *,
    mac_input: str,
) -> None:
    """Test the MAC address is normalized regardless of input format."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_MAC: mac_input,
            CONF_PIN: "1234",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_MAC]).to_equal("AABBCCDDEEFF")
    expect(result["result"].unique_id).to_equal("aa:bb:cc:dd:ee:ff")


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _fumis: MagicMock = Depends(mock_fumis),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the user flow when the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_PIN: "1234",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
