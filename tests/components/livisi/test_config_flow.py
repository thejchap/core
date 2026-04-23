"""Test the Livisi Home Assistant config flow."""

from unittest.mock import patch

from livisi import errors as livisi_errors
from tryke import Depends, expect, fixture, test

from homeassistant.components.livisi.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass, mock_network

from . import (
    VALID_CONFIG,
    mocked_livisi_controller,
    mocked_livisi_login,
    mocked_livisi_setup_entry,
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
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

        expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
        expect(result["title"]).to_equal("SHC Classic")
        expect(result["data"]["host"]).to_equal("1.1.1.1")
        expect(result["data"]["password"]).to_equal("test")


@test.cases(
    test.case(
        "shc_unreachable",
        livisi_errors.ShcUnreachableException(),
        "cannot_connect",
    ),
    test.case(
        "incorrect_ip",
        livisi_errors.IncorrectIpAddressException(),
        "wrong_ip_address",
    ),
    test.case(
        "wrong_credential",
        livisi_errors.WrongCredentialException(),
        "wrong_password",
    ),
)
async def create_entity_after_login_error(
    exception: livisi_errors.LivisiException,
    expected_reason: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
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
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]["base"]).to_equal(expected_reason)
    with mocked_livisi_login(), mocked_livisi_controller(), mocked_livisi_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=VALID_CONFIG,
        )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
