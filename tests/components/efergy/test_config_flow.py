"""Test Efergy config flow."""

from unittest.mock import MagicMock, patch

from pyefergy import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.efergy.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.efergy import (
    CONF_DATA,
    HID,
    _patch_efergy,
    _patch_efergy_status,
    create_entry,
)
from tests.components.efergy._fixtures import mock_zeroconf
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


def _patch_setup():
    return patch("homeassistant.components.efergy.async_setup_entry")


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow."""
    with _patch_efergy(), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal(DEFAULT_NAME)
        expect(result["data"]).to_equal(CONF_DATA)
        expect(result["result"].unique_id).to_equal(HID)


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with unreachable service."""
    with _patch_efergy_status() as efergymock:
        efergymock.side_effect = exceptions.ConnectError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def flow_user_invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with invalid authentication."""
    with _patch_efergy_status() as efergymock:
        efergymock.side_effect = exceptions.InvalidAuth
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("invalid_auth")


@test
async def flow_user_unknown(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test user initialized flow with unknown error."""
    with _patch_efergy_status() as efergymock:
        efergymock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("unknown")


@test
async def flow_reauth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> None:
    """Test reauth step."""
    entry = create_entry(hass)
    result = await entry.start_reauth_flow(hass)
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with _patch_efergy(), _patch_setup():
        new_conf = {CONF_API_KEY: "1234567890"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
        expect(result["type"] is FlowResultType.ABORT).to_be(True)
        expect(result["reason"]).to_equal("reauth_successful")
        expect(entry.data).to_equal(new_conf)
