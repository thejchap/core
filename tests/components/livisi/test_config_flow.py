"""Test the Livisi Home Assistant config flow."""

from unittest.mock import patch

from livisi import errors as livisi_errors
from tryke import Depends, expect, fixture, test

from homeassistant.components.livisi.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    VALID_CONFIG,
    mocked_livisi_controller,
    mocked_livisi_login,
    mocked_livisi_setup_entry,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create LIVISI entity."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with mocked_livisi_login(), mocked_livisi_controller(), mocked_livisi_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("SHC Classic")
        expect(result["data"]["host"]).to_equal("1.1.1.1")
        expect(result["data"]["password"]).to_equal("test")


@test.cases(
    test.case(
        "shc_unreachable",
        exception=livisi_errors.ShcUnreachableException(),
        expected_reason="cannot_connect",
    ),
    test.case(
        "incorrect_ip",
        exception=livisi_errors.IncorrectIpAddressException(),
        expected_reason="wrong_ip_address",
    ),
    test.case(
        "wrong_credential",
        exception=livisi_errors.WrongCredentialException(),
        expected_reason="wrong_password",
    ),
)
async def create_entity_after_login_error(
    exception: livisi_errors.LivisiException,
    expected_reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the LIVISI integration can create an entity after the user had login errors."""
    with patch(
        "homeassistant.components.livisi.config_flow.AioLivisi.async_set_token",
        side_effect=exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_CONFIG
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]["base"]).to_equal(expected_reason)
    with mocked_livisi_login(), mocked_livisi_controller(), mocked_livisi_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_CONFIG,
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
